"use client";

//import { useState } from "react";

const SurveyAppPage = () => {
  //const [firstName, setFirstName] = useState("");

  const handleSubmitSurveyForm = async (event) => {
    // Stop the form from submitting and refreshing the page.
    event.preventDefault();

    //Get data from the form
    const formData = new FormData(event.target);

    const dataToSend = { firstName: formData.get("firstName") };
    //const dataToSend = { firstName }; // Prepare the data to send

    console.log("Data to Send:", dataToSend); //TODO : Verify the structure here

    // Send the data to the server in JSON format.
    const JSONdata = JSON.stringify(dataToSend);

    // API endpoint where we send form data.
    const endpoint = "/api/submit-survey";

    // Form the request for sending data to the server.
    const options = {
      // The method is POST because we are sending data.
      method: "POST",
      // Tell the server we're sending JSON.
      headers: {
        "Content-Type": "application/json",
        "Content-Length": JSONdata.length,
      },
      // Body of the request is the JSON data we created above.
      body: JSONdata,
    };
    // Send the form data to our forms API and get a response.
    const response = await fetch(endpoint, options);

    // Get the response data from server as JSON.
    // If server returns the firstName submitted, that means the form works
    const result = await response.json();
    console.log("Response From Server: ", result);

    // Optionally reset the form
    event.target.reset();
  };

  return (
    <>
      <section>
        <div className={`container border border-primary p-5`}>
          <div className={`row border border-secondary p-4`}>
            <div>
              <div className={`mb-3`}>Contact Us</div>
              <form onSubmit={handleSubmitSurveyForm}>
                <label htmlFor="firstName" className={`form-label`}>
                  First Name
                </label>
                <input
                  id="firstName"
                  name="firstName"
                  //value={firstName}
                  type="text"
                  placeholder="Enter your first name"
                  //onChange={(e) => setFirstName(e.target.value)}
                  required
                  className={`form-control`}
                ></input>
                <button className={`btn btn-primary mt-3`} type="submit">
                  Submit
                </button>
              </form>
            </div>
          </div>
        </div>
      </section>
    </>
  );
};

export default SurveyAppPage;