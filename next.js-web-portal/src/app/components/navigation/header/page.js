"use client";

import Link from "next/link";

import headerStyles from "../../../styles/header.module.css";

const HeaderPage = () => {
  return (
    <>
      <header className={`${headerStyles.headerContainer}`}>
        <nav
          className={`navbar navbar-expand-md ${headerStyles.navbarContainer}`}
        >
          <div className={`container`}>
            <span className={`navbar-brand border ${headerStyles.navbarBrand}`}>
              App Header
            </span>

            <button
              className={`navbar-toggler ${headerStyles.navbarToggler}`}
              type="button"
              data-bs-toggle="collapse"
              data-bs-target="#navbarCollapseContent"
              aria-controls="navbarCollapseContent"
              aria-expanded="false"
              aria-label="Toggle navigation"
            >
              <span className="line"></span>
              <span className="line"></span>
              <span className="line"></span>
            </button>
            <div
              className="collapse navbar-collapse"
              id="navbarCollapseContent"
            >
              <form className={`d-flex border`}>
                <input
                  className={`form-control me-2`}
                  type="search"
                  placeholder="Search"
                  aria-label="Search"
                ></input>
                <button className={`btn btn-outline-success`} type="submit">
                  Search
                </button>
              </form>
              <ul className={`navbar-nav ms-auto border ${headerStyles.navbarNav}`}>
                <li className="nav-item">
                  <Link href="/" className="nav-link">
                    Home
                  </Link>
                </li>
                <li className={`nav-item`}>
                  <Link
                    href={{ pathname: "components/reports" }}
                    className={`nav-link`}
                  >
                    Dashboard
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </nav>
      </header>
    </>
  );
};

export default HeaderPage;