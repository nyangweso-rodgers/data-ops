import Link from "next/link";
import cardStyles from "../../styles/card.module.css";

const dashboardPage = () => {
  return (
    <>
      <section>
        <div className={`container`}>
          <div className={`row`}>
            <div>
              <h1>Welcome to Portal</h1>
            </div>
          </div>
          <div className={`row`}>
            <div className={`col-md-4`}>
              <div>
                <Link
                  href="../components/form/participants-survey"
                  className={`card ${cardStyles.card}`}
                >
                  <div className={`card-body`}>
                    <div>PARTICIPANT'S SURVEY APP</div>
                  </div>
                </Link>
              </div>
            </div>
            <div className={`col-md-4`}>
              <div>
                <Link
                  href="../components/form/delegates-survey"
                  className={`card ${cardStyles.card}`}
                >
                  <div className={`card-body`}>
                    <div>DELEGATES SURVEY APP</div>
                  </div>
                </Link>
              </div>
            </div>
            <div className={`col-md-4`}>
              <div>
                <Link
                  href="../components/market-management/customers"
                  className={`card ${cardStyles.card}`}
                >
                  <div className={`card-body`}>
                    <div>CUSTOMERS APP</div>
                  </div>
                </Link>
              </div>
            </div>
          </div>
          <div className={`row`}></div>
        </div>
      </section>
    </>
  );
};

export default dashboardPage;
