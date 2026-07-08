const { app } = require("@azure/functions");
const axios = require("axios");
const { TableClient } = require("@azure/data-tables");
const { BlobServiceClient } = require("@azure/storage-blob");

app.eventGrid("eventGridTrigger", {
  handler: async (event, context) => {
    context.log("EVENT GRID TRIGGER");

    //--------------------------------------------------
    // Blob information
    //--------------------------------------------------

    const fileUrl = event.data.url;

    const url = new URL(fileUrl);

    const pathParts = url.pathname.split("/");

    const containerName = pathParts[1];

    const blobName = decodeURIComponent(pathParts.slice(2).join("/"));

    const originalFileName = blobName.replace(/_v\d+(?=\.[^.]+$)/, "");

    const extension = originalFileName.includes(".")
      ? originalFileName.split(".").pop().toUpperCase()
      : "UNKNOWN";

    //--------------------------------------------------
    // Category
    //--------------------------------------------------

    let category = "Other";

    switch (extension) {
      case "RVT":
        category = "Revit Model";
        break;

      case "IFC":
        category = "Open BIM";
        break;

      case "DWG":
        category = "CAD Drawing";
        break;

      case "PDF":
        category = "Document";
        break;
    }

    const discipline =
      containerName.charAt(0).toUpperCase() + containerName.slice(1);

    //--------------------------------------------------
    // Read Blob Metadata
    //--------------------------------------------------

    let userEmail = "Unknown";
    let userId = "Unknown";

    try {
      const blobServiceClient = BlobServiceClient.fromConnectionString(
        process.env.AzureWebJobsStorage,
      );

      const blobClient = blobServiceClient
        .getContainerClient(containerName)
        .getBlobClient(blobName);

      const properties = await blobClient.getProperties();

      userEmail = properties.metadata.uploaded_by || "Unknown";

      userId = properties.metadata.user_id || "Unknown";
      const fileSize = Number(
        properties.metadata.file_size || properties.contentLength || 0,
      );
    } catch (error) {
      context.log("Unable to read blob metadata.");

      context.log(error);
    }

    //--------------------------------------------------
    // Azure Table
    //--------------------------------------------------

    let version = 1;

    try {
      const tableClient = TableClient.fromConnectionString(
        process.env.AzureWebJobsStorage,
        "bimmetadata",
      );

      await tableClient.createTable().catch(() => {});

      const previousVersions = [];

      for await (const row of tableClient.listEntities({
        queryOptions: {
          filter: `filename eq '${originalFileName}'`,
        },
      })) {
        previousVersions.push(row);

        if (row.version >= version) version = row.version + 1;
      }

      //--------------------------------------------------
      // Mark previous versions as old
      //--------------------------------------------------

      for (const row of previousVersions) {
        row.is_latest = false;

        await tableClient.updateEntity(row, "Replace");
      }

      //--------------------------------------------------
      // Create new entity
      //--------------------------------------------------

      const entity = {
        partitionKey: discipline,

        rowKey: Date.now().toString(),

        filename: originalFileName,

        blob_name: blobName,

        version: version,

        is_latest: true,

        filetype: extension,

        category: category,

        discipline: discipline,

        container: containerName,

        uploaded_by: userEmail,

        user_id: userId,

        upload_date: new Date().toISOString(),

        file_size: fileSize,
      };

      await tableClient.createEntity(entity);

      context.log(entity);
    } catch (error) {
      context.log("TABLE ERROR");

      context.log(error);
    }

    //--------------------------------------------------
    // Logic App
    //--------------------------------------------------

    try {
      await axios.post(
        process.env.LOGIC_APP_URL,

        {
          filename: originalFileName,

          blob_name: blobName,

          filetype: extension,

          category: category,

          discipline: discipline,

          container: containerName,

          uploaded_by: userEmail,

          user_id: userId,

          upload_date: new Date().toISOString(),

          version: version,

          is_latest: true,
        },
      );

      context.log("Email notification sent.");
    } catch (error) {
      context.log("Email notification failed.");

      context.log(error);
    }

    context.log(`New BIM file uploaded: ${originalFileName}`);
  },
});
