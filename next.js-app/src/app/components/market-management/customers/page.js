"use client";

import pageStyles from "../../../styles/page.module.css";
import formStyles from "../../../styles/form.module.css";
import buttonStyles from "../../../styles/buttons.module.css";

const CustomersPage = () => {
  const handleCustomerRegistration = async (event) => {
    // Stop the form from submitting and refreshing the page.
    event.preventDefault();

    //Get data from thecustomer registration form
    const customerRegistrationFormData = new FormData(event.target);

    const customerFormDataToRegister = Object.fromEntries(
      customerRegistrationFormData
    );

    console.log("Customer Form Data To Register: ", customerFormDataToRegister);

    // Send the data to the server in JSON format.
    const customerRegistrationFormDataInJSON = JSON.stringify(
      customerFormDataToRegister
    );

    // API endpoint where we send form data.
    const customerRegistrationEndpoint = "/api/create-customer";

    // Form the request for sending data to the server.
    const options = {
      // The method is POST because we are sending data.
      method: "POST",
      // Tell the server we're sending JSON.
      headers: {
        "Content-Type": "application/json",
        "Content-Length": customerRegistrationFormDataInJSON.length,
      },
      // Body of the request is the JSON data we created above.
      body: customerRegistrationFormDataInJSON,
    };

    try {
      // Send the form data to our forms API and get a response.
      const response = await fetch(customerRegistrationEndpoint, options);

      // Get the response data from server as JSON.
      const result = await response.json();
      if (response.ok) {
        console.log("Customer Registration is Successful: ", result);

        // Redirect to success page
        {
          /*router.push("/components/messages/success-message");*/
        }
      } else {
        // Handle errors here if necessary
        console.log("Customer Registratio Failed");
      }
    } catch (error) {
      console.log("Error submitting customer registratin form: ", error);
    }

    // Optionally reset the form
    event.target.reset();
  };

  return (
    <>
      <section className={`${pageStyles.section}`}>
        <div className={`container`}>
          <div className={`row ${pageStyles.row}`}>
            <div>
              <h1>Welcome to Customers Application</h1>
            </div>
          </div>
        </div>
        <form className={`container`} onSubmit={handleCustomerRegistration}>
          <div className={`row ${pageStyles.row}`}>
            <div className={`col-md-6`}>
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
            <div className={`col-md-6`}>
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
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div className={`${pageStyles.displayFlexRowCenter}`}>
              <button className={`btn ${buttonStyles.button}`} type="submit">
                Register
              </button>
            </div>
          </div>
        </form>
      </section>
    </>
  );
};

export default CustomersPage;
