import buttonStyles from "../../styles/button.module.css";

const DelegatesSurveyForm = () => {
  return (
    <>
      <main className={`container border border-secondary p-5`}>
        <form>
          <div className={`row border`}>
            <div>
              <h4>CONTACT INFORMATION</h4>
              <p>Please enter your contact information</p>
            </div>
          </div>
          <div className={`row border`}>
            <div>
              <label className={`form-label`}>First Name</label>
              <input type="text" className={`form-control`}></input>
            </div>
          </div>
          <div className={`row border`}>
            <div>
              <label className={`form-label`}>Last Name</label>
              <input type="text" className={`form-control`}></input>
            </div>
          </div>
          <div className={`row border`}></div>
          <div className={`row border`}>
            <div>
              <button
                className={`${buttonStyles.button} ${buttonStyles.submitButton}`}
              >
                Submit
              </button>
            </div>
          </div>
        </form>
      </main>
    </>
  );
};
export default DelegatesSurveyForm;
