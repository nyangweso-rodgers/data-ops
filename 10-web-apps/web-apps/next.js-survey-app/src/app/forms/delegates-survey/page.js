import pageStyles from "../../styles/page.module.css";
import buttonStyles from "../../styles/button.module.css";
import formStyles from "../../styles/form.module.css";

const DelegatesSurveyForm = () => {
  return (
    <>
      <main className={`border border-secondary p-5`}>
        <form className={`container`}>
          <div className={`row ${pageStyles.row}`}>
            <div>
              <h4>CONTACT INFORMATION</h4>
              <p>Please enter your contact information</p>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div>
              <label className={`form-label ${formStyles.label}`}>
                First Name
              </label>
              <input
                type="text"
                className={`form-control ${formStyles.input}`}
              ></input>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div>
              <label className={`form-label ${formStyles.label}`}>
                Last Name
              </label>
              <input
                type="text"
                className={`form-control ${formStyles.input}`}
              ></input>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}></div>
          <div className={`row ${pageStyles.row}`}>
            <div>
              <label className={`form-label ${formStyles.label}`}>
                What should we KEEP doing?
              </label>
              <textarea
                className={`form-control ${formStyles.textarea}`}
                rows={3}
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
export default DelegatesSurveyForm;
