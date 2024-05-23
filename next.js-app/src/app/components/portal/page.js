"use client";

import Link from "next/link";

import pageStyles from "../../styles/page.module.css";

const PortalPage = () => {
  return (
    <>
      <section className={`${pageStyles.section}`}>
        <div className={`container`}>
          <div className={`row`}>
            <div className={`col-md-3`}>
              <div className="">
                <Link
                  href="../components/surveys/participants-survey"
                  className={`card ${pageStyles.card}`}
                >
                  <div className={`card-body`}>
                    <div>CUSTOMER EXPERIENCE</div>
                  </div>
                </Link>
              </div>
            </div>
            <div className={`col-md-3`}>
              <div className="">
                <Link href="#" className={`card ${pageStyles.card}`}>
                  <div className={`card-body`}>
                    <div>MARKET MANAGEMENT</div>
                  </div>
                </Link>
              </div>
            </div>
            <div className={`col-md-3`}>
              <div className="">
                <Link href="#" className={`card ${pageStyles.card}`}>
                  <div className={`card-body`}>
                    <div>ORDER MANAGEMENT</div>
                  </div>
                </Link>
              </div>
            </div>
            <div className={`col-md-3`}>
              <div className="">
                <Link href="#" className={`card ${pageStyles.card}`}>
                  <div className={`card-body`}>
                    <div>ANOTHER MODULE</div>
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
