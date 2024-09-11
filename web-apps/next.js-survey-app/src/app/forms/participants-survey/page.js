import buttonStyles from "../../styles/button.module.css";

const ParticipantsSurveyForm = () => {
  return (
    <>
      <main className="container border border-primary p-5">
        <form>
          <div className={`row`}>
            <div>
              <h4>Contact Information</h4>
            </div>
          </div>
          <div className={`row`}>
            <div className={`col`}>
              <div>
                <label className={`form-label`}>First Name</label>
                <input type="text" className={`form-control`}></input>
              </div>
            </div>
            <div className={`col`}>
              <div>
                <label className={`form-label`}>Last Name</label>
                <input type="text" className={`form-control`}></input>
              </div>
            </div>
          </div>
          <div className={`row`}>
            <div className={`col`}>
              <div>
                <label className={`form-label`}>Email</label>
                <input type="email" className={`form-control`}></input>
              </div>
            </div>
            <div className={`col`}>
              <div>
                <label className={`form-label`}>Phone Number</label>
                <input type="text" className={`form-control`}></input>
              </div>
            </div>
          </div>
          <div className={`row`}>
            <div>
              <h4>Address</h4>
            </div>
          </div>
          <div className={`row`}>
            <div className={`col`}>
              <div>
                <label className={`form-label`}>Nationality</label>
                <select
                  className={`form-select`}
                  name="nationality"
                  id="nationality"
                >
                  <option defaultValue>Select an option</option>
                  <option value="Kenya">Kenya</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>
            <div className={`col`}>
              <div>
                <label className={`form-label`}>City</label>
                <input className={`form-control`} type="text"></input>
              </div>
            </div>
          </div>
          <div className={`row`}>
            <div>
              <label className={`form-label`}>Message</label>
              <textarea className={`form-control`} rows={3}></textarea>
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
        </form>
      </main>
    </>
  );
};
export default ParticipantsSurveyForm;
