"use client";

import pageStyles from "../../styles/page.module.css";

const PortalPage = () => {
  return (
    <>
      <section>
        <div className={`container`}>
          <div className={`row`}>
            <div className={`col-md-3 border`}>
              <div>Module 1</div>
            </div>
            <div className={`col-md-3 border`}>
              <div>Module 2</div>
            </div>
            <div className={`col-md-3 border`}>
              <div>Module 3</div>
            </div>
            <div className={`col-md-3 border`}>
              <div>Module 4</div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
};

export default PortalPage;
