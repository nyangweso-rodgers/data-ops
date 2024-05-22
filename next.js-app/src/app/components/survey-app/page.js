"use client";
import pageStyles from "../../styles/page.module.css";
import utilsStyles from "../../styles/utils.module.css";

//import { useState } from "react";

const SurveyAppPage = () => {
  //const [firstName, setFirstName] = useState("");

  const handleSubmitSurveyForm = async (event) => {
    // Stop the form from submitting and refreshing the page.
    event.preventDefault();

    //Get data from the form
    const formData = new FormData(event.target);
    /*
    const dataToSend = {
      firstName: formData.get("firstName"),
      lastName: formData.get("lastName"),
      emailAddress: formData.get("emailAddress"),
      phoneNumber: formData.get("phoneNumber"),
      message: formData.get("message"),
    };*/
    const dataToSend = Object.fromEntries(formData);

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
    const result = await response.json();
    console.log("Response From Server: ", result);

    // Optionally reset the form
    event.target.reset();
  };

  return (
    <>
      <section className={`${pageStyles.section}`}>
        <div className={`container`}>
          <div className={`row ${pageStyles.row}`}>
            <div className={`mb-3`}>Form Heading</div>
          </div>
        </div>
        <form
          onSubmit={handleSubmitSurveyForm}
          className={`container ${pageStyles.form}`}
        >
          <div className={`row ${pageStyles.row}`}>
            <div className={`col-md-5`}>
              <label
                htmlFor="firstName"
                className={`form-label ${pageStyles.label}`}
              >
                First Name
              </label>
            </div>
            <div className={`col-md-7`}>
              <input
                type="text"
                name="firstName"
                id="firstName"
                className={`form-control ${pageStyles.input}`}
                placeholder="Enter your first name"
                required
              ></input>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <label
              htmlFor="lastName"
              className={`form-label ${pageStyles.label}`}
            >
              Last Name
            </label>
            <input
              type="text"
              name="lastName"
              id="lastName"
              className={`form-control ${pageStyles.input}`}
              placeholder="Enter your last name"
              required
            ></input>
          </div>
          {/*<div className={`row ${pageStyles.row}`}>
            <select name="gender" label="Gender" className="selectpicker">
              <option name="male">Male</option>
              <option name="female">Female</option>
            </select>
          </div>*/}

          <div className={`row ${pageStyles.row}`}>
            <label className={`form-label ${pageStyles.label}`}>Gender</label>
            <div className={`form-check`}>
              <input
                type="radio"
                name="gender"
                id="male"
                value="Male"
                className={`form-check-input`}
              ></input>
              <label className="form-check-label" htmlFor="male">
                Male
              </label>
            </div>
            <div className={`form-check`}>
              <input
                type="radio"
                name="gender"
                id="female"
                value="Female"
                className={`form-check-input`}
              ></input>
              <label className="form-check-label" htmlFor="female">
                Female
              </label>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <label
              htmlFor="emailAddress"
              className={`form-label ${pageStyles.label}`}
            >
              Email Address
            </label>
            <input
              type="email"
              name="emailAddress"
              id="emailAddress"
              className={`form-control ${pageStyles.input}`}
              placeholder="Enter your email address"
              required
            ></input>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <label
              htmlFor="phoneNumber"
              className={`form-label ${pageStyles.label}`}
            >
              Phone
            </label>
            <input
              type="text"
              name="phoneNumber"
              id="phoneNumber"
              className={`form-control ${pageStyles.input}`}
              placeholder="Enter your phone number"
              required
            ></input>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <label
              htmlFor="message"
              className={`form-label ${pageStyles.label}`}
            >
              Message
            </label>
            <textarea
              name="message"
              id="message"
              className={`${pageStyles.textarea}`}
              placeholder="Enter message"
              required
            ></textarea>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <label htmlFor="terms" className={`form-label`}>
              <input id="terms" type="checkbox" />I agree to the terms and
              privacy policy.
            </label>
          </div>

          <div className={`row ${pageStyles.row}`}>
            <div>
              <button className={`btn ${utilsStyles.button}`} type="submit">
                Submit
              </button>
            </div>
          </div>
        </form>
      </section>
    </>
  );
};

export default SurveyAppPage;
