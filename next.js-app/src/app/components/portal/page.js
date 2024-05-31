"use client";

import Link from "next/link";

import pageStyles from "../../styles/page.module.css";
import cardStyles from "../../styles/card.module.css";

const PortalPage = () => {
  return (
    <>
      <section className={`${pageStyles.section}`}>
        <div className={`container`}>
          <div className={`row`}>
            <div className={`col-md-4`}>
              <div className="">
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
              <div className="">
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
                  href="../components/dashboard"
                  className={`card ${cardStyles.card}`}
                >
                  <div className={`card-body`}>
                    <div>DASHBOARD</div>
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
