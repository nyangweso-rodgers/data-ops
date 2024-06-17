import pageStyles from "../../../styles/page.module.css";

const UsersPage = () => {
  return (
    <>
      <section className={`${pageStyles.section}`}>
        <div className={`container`}>
          <div className={`row ${pageStyles.row}`}>
            <div>
              <div>Welcome to Users Application</div>
              <div>Create User</div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
};

export default UsersPage;
