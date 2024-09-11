import pageStyles from "../../styles/page.module.css";
import buttonStyles from "../../styles/button.module.css";
import formStyles from "../../styles/form.module.css";

const ParticipantsSurveyForm = () => {
  return (
    <>
      <main className="border border-primary p-5">
        <form className={`container`}>
          <div className={`row ${pageStyles.row}`}>
            <div>
              <h4>Contact Information</h4>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div className={`col-md-6`}>
              <div>
                <label className={`form-label ${formStyles.label}`}>
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
                <label className={`form-label ${formStyles.label}`}>
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
                <label className={`form-label ${formStyles.label}`}>
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
                <label className={`form-label ${formStyles.label}`}>
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
                <label className={`form-label ${formStyles.label}`}>
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
                <label className={`form-label ${formStyles.label}`}>City</label>
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
              <label className={`form-label ${formStyles.label}`}>
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
              <label className={`form-label ${formStyles.label}`}>
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
              <label className={`form-label ${formStyles.label}`}>
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
        </form>
      </main>
    </>
  );
};
export default ParticipantsSurveyForm;
