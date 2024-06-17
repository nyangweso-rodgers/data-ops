import pageStyles from "../../../styles/page.module.css";

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
            <div>
              <div></div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
};

export default CustomersPage;
