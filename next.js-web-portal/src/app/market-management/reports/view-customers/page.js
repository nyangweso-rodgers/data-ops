//"use client";

import pageStyles from "../../../styles/page.module.css";
import tableStyles from "../../../styles/table.module.css";

export default async function CustomersDashboardPage() {
  const res = await fetch("http://localhost:3003/api/get-customer");

  if (!res.ok) {
    // This will activate the closest `error.js` Error Boundary.
    throw new Error(`Failed to fetch customer data`);
  }

  const customerData = await res.json();
  console.log("Customers Data to be displayed: ", customerData);

  return (
    <>
      <section className={`${pageStyles.section}`}>
        <div className={`container`}>
          <div className={`row ${pageStyles.row}`}>
            <div>Customers Report</div>
          </div>

          <div className={`row ${pageStyles.row}`}>
            <div>
              <div>
                <table
                  className={`table table-striped table-hover table table-bordered`}
                >
                  <thead className={`${tableStyles.tableHeader}`}>
                    <tr>
                      <th>Id</th>
                      <th>First Name</th>
                      <th>Last Name</th>
                      <th>Status</th>
                      <th>Creation Date</th>
                      <th>Date Updated</th>
                    </tr>
                  </thead>
                  <tbody>
                    {customerData.map((data) => (
                      <tr key={data.id}>
                        <td>{data.id}</td>
                        <td>{data.first_name}</td>
                        <td>{data.last_name}</td>
                        <td>{data.status}</td>
                        <td>{data.createdAt}</td>
                        <td>{data.updatedAt}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
