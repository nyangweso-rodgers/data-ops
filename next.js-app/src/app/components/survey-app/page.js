"use client";

const submitFormData = async (event) => {
  event.preventDefault();

  const firstName = event.target.firstNameInput.value;

  // Prepare the data to send to the API route
  const formData = {
    firstName: firstName,
    // Add other form fields here as needed
  };
  try {
    // Make an HTTP POST request to the API route
    const response = await fetch("../../api/submit-survey", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formData),
    });
    // Check if the request was successful
    if (response.ok) {
      // Handle the response if needed
      const responseData = await response.json();
      console.log(responseData);
    } else {
      // Handle errors if the request fails
      throw new Error(`HTTP error! Status: ${response.status}`);
    }
  } catch (error) {
    // Handle network errors or other exceptions
    console.error("Error submitting form:", error);
  }
};
const SurveyAppPage = () => {
  return (
    <>
      <section>
        <div className={`container border border-primary p-5`}>
          <div className={`row border border-secondary p-4`}>
            <div>
              <div className={`mb-3`}>Contact Us</div>
              <form onSubmit={submitFormData}>
                <label htmlFor="firstNameInput" className={`form-label`}>
                  First Name
                </label>
                <input id="firstNameInput" className={`form-control`}></input>
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