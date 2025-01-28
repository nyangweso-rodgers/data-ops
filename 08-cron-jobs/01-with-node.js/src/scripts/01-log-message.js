import express from "express";
import cron from "node-cron";

//initialize the express
const app = express();

//function your made
const testMessage = () => {
  console.log("job executed on:", new Date().toLocaleString());
};

// cron schedule
cron.schedule("* * * * * *", function () {
  try {
    testMessage();
  } catch (error) {
    console.error("Error occurred during CRON job:", error);
  }
});

// Start the server
const PORT = 3007;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
