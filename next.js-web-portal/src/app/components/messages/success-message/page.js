"use client";

import Link from "next/link";

//import { useRouter } from "next/router";

import pageStyles from "../../../styles/page.module.css";
import utilsStyles from "../../../styles/utils.module.css";

const SuccessMessagePage = () => {
  return (
    <>
      <section className={pageStyles.section}>
        <div className={`container`}>
          <div className={`row ${pageStyles.row}`}>
            <div className="mb-3">
              <h1>Your response has been successfully recorded. Thank you!</h1>
            </div>
          </div>
          <div className={`row ${pageStyles.row}`}>
            <div className="mb-3">
              <Link href="/" className={`btn ${utilsStyles.button}`}>
                Go Back
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  );
};

export default SuccessMessagePage;
