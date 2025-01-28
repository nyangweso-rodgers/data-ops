# Scheduling Tasks with CRON Jobs in Node.js

- Prerequisites:
  1. Node.js
  2. Npm

# Steps to Create a CRON Job in Node.js

1. Step 1: Create a Node.js Project

   - Initialize a new Node.js project or use an existing one

2. Step 2: **Install packages**

   - Install the following packages
     ```sh
        npm i node-cron express
     ```

3. **Step 3**: **Writing the Cron Job**

   - Create a function to be executed on a schedule.
   - **Example 1**: log a message to the console:
     ```js
     function logMessage() {
       console.log("Job executed on:", new Date().toLocaleString());
     }
     ```
   - Execute the function: Once the function is defined, we can execute it on interval
   - The Syntax for the CRON Job is:
     ```javascript
     cron.schedule("* * * * *", function () {
       // Task
     });
     ```
   - Where, every asterisk defines something: The **asterisk** depicts the **Second**, **Minute**, **Hour**, **Day**, **Month**, and **Week** respectively from the left

     1. Second — optional
     2. Minute: 0–59
     3. Hour: 0–23
     4. Day of the Month: 1–31
     5. Month: 1–12
     6. Day of the week: 0–7 (0 and 7 both represent Sunday)

   - Example:
     - `( * * * * * )` — runs every minute
     - `( 0 * * * * )` — runs every hour
     - `( 0 15 15 * * )` — runs every month on the 15th at 3 pm
     - `( * * 5 * * )` — runs every 5th of the month

# Examples:

1. Daily Cleanup at midnight

   ```js
   cron.schedule("0 0 * * *", () => {
     console.log("Running a job at midnight");
     // Add your cleanup code here
   });
   ```

2. Weekly Report Generation on Mondays
   ```javascript
   cron.schedule("0 9 * * 1", () => {
     console.log("Generating weekly report");
     // Add report generation code here
   });
   ```

# Resources and Further Reading

1. [Medium - Scheduling Tasks with CRON Jobs in Node.js](https://medium.com/@surajAherrao/scheduling-tasks-with-cron-jobs-in-node-js-85680383a659)
