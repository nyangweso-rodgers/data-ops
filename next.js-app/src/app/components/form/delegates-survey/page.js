"use client";

import pageStyles from "../../../styles/page.module.css";
import formStyles from "../../../styles/form.module.css";
//import utilsStyles from "../../../styles/utils.module.css";
import buttonStyles from "../../../styles/buttons.module.css";

const DelegatesSurveyPage = () => {
  const handleSubmitDelegatesSurveyForm = async (event) => {
    // Stop the form from submitting and refreshing the page.
    event.preventDefault();

    //Get data from the form
    const delegatesSurveyFormData = new FormData(event.target);

    const delegatesSurveyFormDataToSubmit = Object.fromEntries(
      delegatesSurveyFormData
    );

    console.log(
      "Delegates Survey Form Data To Submit: ",
      delegatesSurveyFormDataToSubmit
    );

    // Send the data to the server in JSON format.
    const delegatesSurveyFormDataInJSON = JSON.stringify(
      delegatesSurveyFormDataToSubmit
    );

    // API endpoint where we send form data.
    const delegatesSurveyEndpoint = "/api/submit-delegates-survey";

    // Form the request for sending data to the server.
    const options = {
      // The method is POST because we are sending data.
      method: "POST",
      // Tell the server we're sending JSON.
      headers: {
        "Content-Type": "application/json",
        "Content-Length": delegatesSurveyFormDataInJSON.length,
      },
      // Body of the request is the JSON data we created above.
      body: delegatesSurveyFormDataInJSON,
    };

    try {
      // Send the form data to our forms API and get a response.
      const response = await fetch(delegatesSurveyEndpoint, options);

      // Get the response data from server as JSON.
      const result = await response.json();
      if (response.ok) {
        console.log("Delegates Form Submission Successful: ", result);

        // Redirect to success page
        {
          /*router.push("/components/messages/success-message");*/
        }
      } else {
        // Handle errors here if necessary
        console.log("Delegates Form Submission Failed");
      }
    } catch (error) {
      console.log("Error submitting Delegates form: ", error);
    }

    // Optionally reset the form
    event.target.reset();
  };

  return (
    <>
      <section className={`${pageStyles.section}`}>
        <form
          onSubmit={handleSubmitDelegatesSurveyForm}
          className={`container ${formStyles.form}`}
        >
          <div className={`row ${pageStyles.row}`}>
            <div>
              <label
                htmlFor="first_name"
                className={`form-label ${formStyles.label}`}
              >
                First Name
              </label>
            </div>
            <div>
              <input
                type="text"
                name="first_name"
                id="first_name"
                className={`form-control ${formStyles.input}`}
                placeholder="Enter your first name"
                required
              ></input>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div>
              <label
                htmlFor="last_name"
                className={`form-label ${formStyles.label}`}
              >
                Last Name
              </label>
            </div>
            <div>
              <input
                type="text"
                name="last_name"
                id="last_name"
                className={`form-control ${formStyles.input}`}
                placeholder="Enter your last name"
                required
              ></input>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div>
              <label
                htmlFor="company_name"
                className={`form-label ${formStyles.label}`}
              >
                Company/Organization Name
              </label>
            </div>
            <div>
              <input
                type="text"
                name="company_name"
                id="company_name"
                className={`form-control ${formStyles.input}`}
                placeholder="Enter your company name"
                required
              ></input>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div className={`${pageStyles.displayFlexRowCenter}`}>
              <button className={`btn ${buttonStyles.button}`} type="submit">
                Submit
              </button>
              {/*<Link
                type="submit"
                href="/components/messages/success-message"
                onClick={() => {
              router.push("../components/messages/success-message")
                }}
                className={`btn ${utilsStyles.button}`}
              >
                Submit
              </Link>*/}
            </div>
          </div>
        </form>
      </section>
    </>
  );
};

export default DelegatesSurveyPage;
