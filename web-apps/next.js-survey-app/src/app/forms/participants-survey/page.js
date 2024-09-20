"use client";

import React, { useState } from "react";

import pageStyles from "../../styles/page.module.css";
import buttonStyles from "../../styles/button.module.css";
import formStyles from "../../styles/form.module.css";
//import { headers } from "next/headers";

const ParticipantsSurveyForm = () => {
  const [formStatus, setFormStatus] = useState(null); // To track form submission status

  const handleParticipantSurveyForm = async (event) => {
    // Stop the form from submitting and refreshing the page.
    event.preventDefault();

    // get data from form
    const participantSurveyFormData = new FormData(event.target);

    const participantSurveyFormEntries = Object.fromEntries(
      participantSurveyFormData
    );

    console.log(
      "Participant's Survey Form Entries: ",
      participantSurveyFormEntries
    );

    // Send the data to the server in JSON format
    const participantSurveyFormJsonData = JSON.stringify(
      participantSurveyFormEntries
    );

    // API endpoint where we send form data.
    const createParticipantSurveyEndpoint =
      "/api/participant-survey/create-participant-survey";

    const options = {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: participantSurveyFormJsonData,
    };
    try {
      // Send the form data to our forms API and get a response.
      const response = await fetch(createParticipantSurveyEndpoint, options);

      // Get the response data from server as JSON.
      const result = await response.json();

      if (response.ok) {
        setFormStatus("success"); // Display success feedback
        console.log("Participants Survey Form Submission Successful: ", result);
      } else {
        setFormStatus("error"); // Display error feedback
        console.log("Participants Survey Form Submission Failed");
      }
    } catch (error) {
      setFormStatus("error");
      console.log("Error Submitting Participants Survey Form: ", error);
    }
    // Optionally reset the form
    event.target.reset();
  };
  return (
    <>
      <main className="">
        <form onSubmit={handleParticipantSurveyForm} className={`container`}>
          <div className={`row ${pageStyles.row}`}>
            <div>
              <h4>Contact Information</h4>
              <p>Please enter your contact information.</p>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div className={`col-md-6`}>
              <div>
                <label
                  htmlFor="firstName"
                  className={`form-label ${formStyles.label}`}
                >
                  First Name
                </label>
                <input
                  className={`form-control ${formStyles.input}`}
                  type="text"
                  id="firstName"
                  name="firstName"
                ></input>
              </div>
            </div>
            <div className={`col-md-6`}>
              <div>
                <label
                  htmlFor="lastName"
                  className={`form-label ${formStyles.label}`}
                >
                  Last Name
                </label>
                <input
                  className={`form-control ${formStyles.input}`}
                  type="text"
                  id="lastName"
                  name="lastName"
                ></input>
              </div>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div className={`col-md-6`}>
              <div>
                <label
                  htmlFor="emailAddress"
                  className={`form-label ${formStyles.label}`}
                >
                  Email
                </label>
                <input
                  className={`form-control ${formStyles.input}`}
                  type="email"
                  id="emailAddress"
                  name="emailAddress"
                ></input>
              </div>
            </div>
            <div className={`col-md-6`}>
              <div>
                <label
                  htmlFor="phoneNumber"
                  className={`form-label ${formStyles.label}`}
                >
                  Phone Number
                </label>
                <input
                  className={`form-control ${formStyles.input}`}
                  type="text"
                  id="phoneNumber"
                  name="phoneNumber"
                ></input>
              </div>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div>
              <h4>Address</h4>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div className={`col-md-6`}>
              <div>
                <label
                  htmlFor="nationality"
                  className={`form-label ${formStyles.label}`}
                >
                  Nationality
                </label>
                <select
                  className={`form-select ${formStyles.select}`}
                  name="nationality"
                  id="nationality"
                >
                  <option defaultValue>Select an option</option>
                  <option value="Kenya">Kenya</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>
            <div className={`col-md-6`}>
              <div>
                <label
                  htmlFor="city"
                  className={`form-label ${formStyles.label}`}
                >
                  City
                </label>
                <input
                  className={`form-control ${formStyles.input}`}
                  type="text"
                  id="city"
                  name="city"
                ></input>
              </div>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div>
              <label
                htmlFor="keepDoing"
                className={`form-label ${formStyles.label}`}
              >
                What should we KEEP doing?
              </label>
              <textarea
                className={`form-control ${formStyles.textarea}`}
                rows={3}
                placeholder="Type your message"
                id="keepDoing"
                name="keepDoing"
              ></textarea>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div>
              <label
                htmlFor="startDoing"
                className={`form-label ${formStyles.label}`}
              >
                What should we START doing?
              </label>
              <textarea
                className={`form-control ${formStyles.textarea}`}
                rows={3}
                id="startDoing"
                name="startDoing"
              ></textarea>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div>
              <label
                htmlFor="stopDoing"
                className={`form-label ${formStyles.label}`}
              >
                What should we STOP doing?
              </label>
              <textarea
                className={`form-control ${formStyles.textarea}`}
                rows={3}
                id="stopDoing"
                name="stopDoing"
              ></textarea>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div className={`${pageStyles.flexRowCenter}`}>
              <button
                className={`${buttonStyles.button} ${buttonStyles.submitButton}`}
                type="submit"
              >
                Submit
              </button>
            </div>
          </div>
          {/* Display feedback after submission */}
          {formStatus === "success" && (
            <p className="text-success">Form submitted successfully!</p>
          )}
          {formStatus === "error" && (
            <p className="text-danger">
              Failed to submit the form. Please try again.
            </p>
          )}
        </form>
      </main>
    </>
  );
};
export default ParticipantsSurveyForm;
