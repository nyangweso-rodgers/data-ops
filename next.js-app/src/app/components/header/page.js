"use client";

import Link from "next/link";

import headerStyles from "../../styles/header.module.css";

const HeaderPage = () => {
  return (
    <>
      <header className={`${headerStyles.header}`}>
        <nav className={`navbar navbar-expand-md ${headerStyles.navbar}`}>
          <div className={`container`}>
            <a className={`navbar-brand ${headerStyles.headerBrand}`} href="/">
              Rodgers Nyangweso
            </a>
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
              <ul className={`navbar-nav ms-auto ${headerStyles.navbarNav}`}>
                <li className="nav-item">
                  <Link href="/" className="nav-link">
                    Home
                  </Link>
                </li>
                <li className="nav-item">
                  <Link href="#" className="nav-link">
                    Content
                  </Link>
                </li>
                <li className="nav-item">
                  <Link href="#" className="nav-link">
                    Another Content
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
