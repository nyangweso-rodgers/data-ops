import prisma from "../../../lib/prisma";
import pageStyles from "../../../styles/page.module.css";
import tableStyles from "../../../styles/table.module.css";

// Render per request: the data lives in Postgres, so don't prerender at build time.
export const dynamic = "force-dynamic";

export default async function CustomersDashboardPage() {
  // Server component: query the DB directly instead of calling our own /api route.
  // A failure here activates the closest `error.js` Error Boundary.
  const customerData = await prisma.customer.findMany();

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
                        <td>{data.created_at.toISOString()}</td>
                        <td>{data.updated_at.toISOString()}</td>
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
