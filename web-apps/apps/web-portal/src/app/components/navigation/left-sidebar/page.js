"use client";

import Link from "next/link";
import layoutStyles from "../../../styles/layout.module.css";

const LeftSidebarPage = () => {
  return (
    <>
      <section className={``}>
        <nav className={``}>
          <ul className={`${layoutStyles.unorderedList}`}>
            <li>
              <Link href="#">Home</Link>
            </li>
            <li>
              <Link href="/dashboard">Dashboard</Link>
            </li>
            <li>
              <span>Marketing</span>
              <ul>
                <li>
                  <Link href="/marketing/forms/register-delegates">
                    Deligates Registration
                  </Link>
                </li>
                <li>
                  <Link href="/marketing/forms/delegates-survey">
                    Deligates Survey
                  </Link>
                </li>
                <li>
                  <Link href="/marketing/forms/participants-survey">
                    Participants Survey
                  </Link>
                </li>
                <li>
                  <span>Reports</span>
                  <ul>
                    <li>
                      <Link href="/marketing-reports/view-registered-delegates">
                        View Registered Delegates
                      </Link>
                    </li>
                    <li>
                      <Link href="/marketing-reports/view-delegates-survey">
                        View Delegates Survey
                      </Link>
                    </li>
                    <li>
                      <Link href="/marketing-reports/view-participants-survey">
                        View Participant's Survey
                      </Link>
                    </li>
                  </ul>
                </li>
              </ul>
            </li>
            <li>
              <span>Market Management</span>
              <ul>
                <li>
                  <Link href="/market-management/form/register-customer">
                    Register Customer
                  </Link>
                </li>
                <li>
                  <span>Reports</span>
                  <ul>
                    <li>
                      <Link href="/market-management/reports/view-customers">
                        View Customers
                      </Link>
                    </li>
                  </ul>
                </li>
              </ul>
            </li>
            <li>
              <span>Sales</span>
              <ul>
                <li>
                  <Link href="#">Payments</Link>
                </li>
              </ul>
            </li>
          </ul>
        </nav>
      </section>
    </>
  );
};

export default LeftSidebarPage;
