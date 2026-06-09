// const { app } = require("@azure/functions");

// app.storageBlob("storageBlobTrigger", {
//   path: "architecture/{name}",
//   connection: "AzureWebJobsStorage",

//   handler: async (blob, context) => {
//     const fileName = context.triggerMetadata.name;

//     const metadata = {
//       filename: fileName,
//       upload_date: new Date().toISOString(),
//       discipline: "architecture",
//     };

//     context.log("BIM File Metadata:");
//     context.log(metadata);

//     const notificationMessage = `New BIM file uploaded: ${fileName}`;

//     context.log(notificationMessage);
//   },
// });

const { app } = require("@azure/functions");
const axios = require("axios");
const { TableClient } = require("@azure/data-tables");
app.storageBlob("storageBlobTrigger", {
  path: "architecture/{name}",
  connection: "AzureWebJobsStorage",

  handler: async (blob, context) => {
    const fileName = context.triggerMetadata?.name || "unknown";

    const extension = fileName.includes(".")
      ? fileName.split(".").pop().toUpperCase()
      : "UNKNOWN";

    let category = "Other";
    let discipline = "Unknown";

    // File type category
    if (extension === "RVT") {
      category = "Revit Model";
    } else if (extension === "IFC") {
      category = "Open BIM";
    } else if (extension === "DWG") {
      category = "CAD Drawing";
    } else if (extension === "PDF") {
      category = "Document";
    }

    // Discipline detection from file name
    const lowerFileName = fileName.toLowerCase();

    if (lowerFileName.includes("arch")) {
      discipline = "Architecture";
    } else if (lowerFileName.includes("struct")) {
      discipline = "Structure";
    } else if (lowerFileName.includes("mep")) {
      discipline = "MEP";
    } else if (lowerFileName.includes("hvac")) {
      discipline = "HVAC";
    } else if (lowerFileName.includes("elect")) {
      discipline = "Electrical";
    } else if (lowerFileName.includes("plumb")) {
      discipline = "Plumbing";
    } else if (lowerFileName.includes("civil")) {
      discipline = "Civil";
    } else if (lowerFileName.includes("land")) {
      discipline = "Landscape";
    }

    const metadata = {
      filename: fileName,
      filetype: extension,
      category: category,
      discipline: discipline,
      upload_date: new Date().toISOString(),
    };
    context.log("START TABLE WRITE");
    const connectionString = process.env.AzureWebJobsStorage;
    context.log(`Connection string exists: ${!!connectionString}`);

    try {
      const tableClient = TableClient.fromConnectionString(
        process.env.AzureWebJobsStorage,
        "bimmetadata",
      );

      await tableClient.createTable().catch(() => {});

      const entity = {
        partitionKey: metadata.discipline,
        rowKey: Date.now().toString(),
        filename: metadata.filename,
        filetype: metadata.filetype,
        category: metadata.category,
        upload_date: metadata.upload_date,
      };

      await tableClient.createEntity(entity);

      context.log("TABLE ENTITY CREATED");
      context.log(entity);
    } catch (error) {
      context.log("TABLE ERROR");
      context.log(error);
    }
    await axios.post(
      "https://prod-11.polandcentral.logic.azure.com:443/workflows/e204421431604be2b51b256d5ab9a738/triggers/When_an_HTTP_request_is_received/paths/invoke?api-version=2016-10-01&sp=%2Ftriggers%2FWhen_an_HTTP_request_is_received%2Frun&sv=1.0&sig=ngexGPZQLIha0BcM_heCsdrawgWPz1UVPZhwMq2KVeI",
      metadata,
    );

    context.log("BIM File Metadata:");
    context.log(metadata);

    context.log(`New BIM file uploaded: ${fileName}`);
  },
});
