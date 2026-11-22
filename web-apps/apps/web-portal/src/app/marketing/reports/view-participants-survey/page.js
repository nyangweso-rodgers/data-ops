import connectToMongoDB from "../../../utils/participants-survey-mongodb-connection.js";
import ParticipatsSurveyModel from "../../../model/participants-survey-schema.js";
import pageStyles from "../../../styles/page.module.css";
import tableStyles from "../../../styles/table.module.css";

// Render per request: the data lives in MongoDB, so don't prerender at build time.
export const dynamic = "force-dynamic";

export default async function ParticipantsSurveyReportPage() {
  // Server component: query the DB directly instead of calling our own /api route.
  // A failure here activates the closest `error.js` Error Boundary.
  await connectToMongoDB();
  const participantsSurveyData = await ParticipatsSurveyModel.find().lean();

  return (
    <>
      <section className={`${pageStyles.section}`}>
        <div className={`container`}>
          <div className={`row ${pageStyles.row}`}>
            <div>Participant&apos;s Survey Report</div>
          </div>
          {/* Return a Table */}
          <div className={`row ${pageStyles.row}`}>
            <div>
              <table
                className={`table table-striped table-hover table table-bordered`}
              >
                <thead className={`${tableStyles.tableHeader}`}>
                  <tr>
                    <th>Code</th>
                    <th>First Name</th>
                    <th>Last Name</th>
                    <th>Nationality</th>
                    <th>Current Residence</th>
                    <th>Gender</th>
                    <th>Agreed To Terms</th>
                  </tr>
                </thead>
                <tbody>
                  {participantsSurveyData.map((data) => (
                    <tr key={String(data._id)}>
                      <td>{data.code}</td>
                      <td>{data.firstName}</td>
                      <td>{data.lastName}</td>
                      <td>{data.nationality}</td>
                      <td>{data.currentResidence}</td>
                      <td>{data.gender}</td>
                      <td>{data.agreedToTerms ? "Yes" : "No"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Return a List */}

          {/*
          <div className={`row ${pageStyles.row}`}>
            <div>
              <ul>
                {participantsSurveyData.map((data) => (
                  <li key={data._id}>{data.code}</li>
                ))}
              </ul>
            </div> table table-bordered
          </div>
          */}

          {/* Return a List */}

          {/*
          <div className={`row ${pageStyles.row}`}>
            <div>
              <ul>
                {participantsSurveyData.map((data) => (
                  <li key={data.id}>{data.title}</li>
                ))}
              </ul>
            </div>
          </div>
          */}
          {/* Return a Table */}

          {/*<div className={`row ${pageStyles.row}`}>
            <div>
              <table
                className={`table table-striped table-hover table table-bordered`}
              >
                <thead className={`${tableStyles.tableHeader}`}>
                  <tr>
                    <th>ID</th>
                    <th>User Id</th>
                    <th>Title</th>
                  </tr>
                </thead>
                <tbody>
                  {participantsSurveyData.map((data) => (
                    <tr key={data.id}>
                      <td>{data.id}</td>
                      <td>{data.userId}</td>
                      <td>{data.title}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>*/}
        </div>
      </section>
    </>
  );
}