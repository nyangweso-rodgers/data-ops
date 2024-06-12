import Link from "next/link";

import pageStyles from "../../styles/page.module.css";
import cardStyles from "../../styles/card.module.css";

const ReportsPage = () => {
  return (
    <>
      <section className={`${pageStyles.section}`}>
        <div className={`container`}>
          <div className={`row`}>
            <div className={`col-md-4`}>
              <div>
                <Link
                  href={{
                    pathname: "/components/reports/participants-survey-report",
                  }}
                  className={`card ${cardStyles.card}`}
                >
                  Participant's Survey Report
                </Link>
              </div>
            </div>
            <div className={`col-md-4`}>
              <div>
                <Link
                  href={{
                    pathname: "/components/reports/delegates-survey-report",
                  }}
                  className={`card ${cardStyles.card}`}
                >
                  Delegates Survey Report
                </Link>
              </div>
            </div>
            <div className={`col-md-4`}>
              <div>
                <Link
                  href={{ pathname: "/components/reports/customers-report" }}
                  className={`card ${cardStyles.card}`}
                >
                  Customers Report
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
};

export default ReportsPage;
