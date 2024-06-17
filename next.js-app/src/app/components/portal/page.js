"use client";

import Link from "next/link";

import pageStyles from "../../styles/page.module.css";
import cardStyles from "../../styles/card.module.css";

const PortalPage = () => {
  return (
    <>
      <section className={`${pageStyles.section}`}>
        <div className={`container`}>
          <div className={`row ${pageStyles.row}`}>
            <div>
              <div>Welcome to Portal</div>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div className={`col-md-4`}>
              <div>
                <Link
                  href="../components/surveys/participants-survey"
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
                  href="../components/surveys/delegates-survey"
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
          <div className={`row ${pageStyles.row}`}>
            <div className={`col`}>
              <div>
                <Link
                  href="../components/reports"
                  className={`card ${cardStyles.card}`}
                >
                  <div className={`card-body`}>
                    <div>REPORTS</div>
                  </div>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
};

export default PortalPage;
