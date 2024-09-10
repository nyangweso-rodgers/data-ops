import buttonStyles from "../../styles/button.module.css";

const ParticipantsSurveyForm = () => {
  return (
    <>
      <main className="border p-5">
        <div className={`row`}>
          <div>
            <h2>Contact Information</h2>
          </div>
        </div>
        <div className={`row`}>
          <div>
            <h2>Address</h2>
          </div>
        </div>
        <div className={`row border`}>
          <div>
            <button
              className={`${buttonStyles.button} ${buttonStyles.submitButton}`}
            >
              Submit
            </button>
          </div>
        </div>
      </main>
    </>
  );
};
export default ParticipantsSurveyForm;
