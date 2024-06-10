import Link from "next/link";

import pageStyles from "../../styles/page.module.css";
import cardStyles from "../../styles/card.module.css";

const ReportsPage = () => {
  return (
    <>
      <section className={`${pageStyles.section}`}>
        <div className={`container`}>
          <div className={`row`}>
            <div className={`col-md-6`}>
              <div>
                <Link
                  href="./participants/"
                  className={`card ${cardStyles.card}`}
                >
                  Participant's Survey Report
                </Link>
              </div>
            </div>
            <div className={`col-md-6`}>
              <div>
                <Link href="#" className={`card ${cardStyles.card}`}>
                  Delegates Survey Report
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
