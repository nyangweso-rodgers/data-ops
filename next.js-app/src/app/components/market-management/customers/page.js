import pageStyles from "../../../styles/page.module.css";
import formStyles from "../../../styles/form.module.css";
import buttonStyles from "../../../styles/buttons.module.css";

const CustomersPage = () => {
  return (
    <>
      <section className={`${pageStyles.section}`}>
        <div className={`container`}>
          <div className={`row ${pageStyles.row}`}>
            <div>
              <div>Welcome to Customers Application</div>
              <div>Register User</div>
            </div>
          </div>
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
          <div className={`row ${pageStyles.row} `}>
            <div className={`${pageStyles.displayFlexRowCenter}`}>
              <button className={`btn ${buttonStyles.button}`} type="submit">
                Register
              </button>
            </div>
          </div>
        </div>
      </section>
    </>
  );
};

export default CustomersPage;
