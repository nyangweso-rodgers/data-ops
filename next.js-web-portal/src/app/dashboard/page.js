import tableStyles from "../styles/table.module.css";

const DashboardPage = () => {
  return (
    <>
      <section>
        <div className={`container border`}>
          <div className={`row`}>
            <div>
              <table className={`${tableStyles.table}`}>
                <caption>Annual surface temperature change in 2022</caption>
                <thead className={`${tableStyles.tableHead}`}>
                  <tr>
                    <th scope="column">Country</th>
                    <th scope="column">Mean temperature change (°C)</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <th scope="row">United Kingdom</th>
                    <td>1.912</td>
                  </tr>
                  <tr>
                    <th scope="row">Afghanistan</th>
                    <td>2.154</td>
                  </tr>
                </tbody>
                <tfoot className={`${tableStyles.tableFooter}`}>
                  <tr>
                    <th scope="row">Global average</th>
                    <td>1.4</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>
      </section>
    </>
  );
};

export default DashboardPage;
