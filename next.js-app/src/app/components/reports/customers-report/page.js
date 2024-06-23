import pageStyles from "../../../styles/page.module.css";

const CustomersSurveyReportPage = () => {
  return (
    <>
      <section className={`${pageStyles.section}`}>
        <div className={`container`}>
          <div className={`row ${pageStyles.row}`}>
            <div>Customers Report</div>
          </div>
          <div className={`row`}>
            <div>Display customer report here</div>
          </div>
        </div>
      </section>
    </>
  );
};

export default CustomersSurveyReportPage;