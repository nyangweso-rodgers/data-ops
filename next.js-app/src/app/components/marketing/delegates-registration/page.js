import pageStyles from "../../../styles/page.module.css";
import formStyles from "../../../styles/form.module.css";
//import utilsStyles from "../../../styles/utils.module.css";
import buttonStyles from "../../../styles/buttons.module.css";

const DelegatesRegistrationFormPage = () => {
  return (
    <>
      <section className={`${pageStyles.section}`}>
        <div className={`container`}>
          <div className={`row`}>
            <div>
              <h2>
                Please fill out the below registratio form to attend Delegates
                Conference 2024 - Kenya on 10-15 August.
              </h2>
            </div>
          </div>
        </div>
        <form className={`container`}>
          <div className={`row ${pageStyles.row}`}>
            <div className={`col-md-6`}>
              <label className={`form-label ${formStyles.formLabel}`}>
                First Name
              </label>
              <input
                className={`form-control ${formStyles.formInput}`}
                type="text"
              ></input>
            </div>
            <div className={`col-md-6`}>
              {" "}
              <label className={`form-label`}>Last Name</label>
              <input className={`form-control`} type="text"></input>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div className={`col-md-6`}>
              {" "}
              <label className={`form-label`}>Official Email</label>
              <input className={`form-control`}></input>
            </div>
            <div className={`col-md-6`}>
              <label className={`form-label`}>Mobile number</label>
              <select className={`form-select`}>
                <option defaultValue>Kenya</option>
                <option>Uganda</option>
              </select>
              <input className={`form-control`} type="text"></input>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div className={`col-md-6`}>
              {" "}
              <label className={`form-label`}>Job Title</label>
              <input className={`form-control`} type="text"></input>
            </div>
            <div className={`col-md-6`}>
              {" "}
              <label className={`form-label`}>Company Name</label>
              <input className={`form-control`} type="text"></input>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div className={`col-md-6`}>
              {" "}
              <label className={`form-label`}>Industry</label>
              <input className={`form-control`} type="text"></input>
            </div>
            <div className={`col-md-6`}>
              {" "}
              <label className={`form-label`}>Role/Authority</label>
              <input className={`form-control`} type="text"></input>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div className={`col`}>
              <div>
                <button
                  className={`btn ${buttonStyles.submitButton}`}
                  type="submit"
                >
                  Register
                </button>
              </div>
            </div>
          </div>
        </form>
      </section>
    </>
  );
};

export default DelegatesRegistrationFormPage;
