import pageStyles from "../../../styles/page.module.css";
import tableStyles from "../../../styles/table.module.css";

export default async function ParticipantsSurveyReportPage() {
  //const res = await fetch("https://jsonplaceholder.typicode.com/posts"); //TODO: Endpoint for testing

  //const res = await fetch("/api/get-participants-survey");
  //const res = await fetch("/api/get-participants-survey/");

  const res = await fetch("http://localhost:3003/api/get-participants-survey");

  //const res = await fetch("../../../api/get-participants-survey");

  if (!res.ok) {
    // This will activate the closest `error.js` Error Boundary.
    throw new Error(`Failed to fetch participants survey data`);
  }

  const participantsSurveyData = await res.json();
  console.log("participantsSurveyData: ", participantsSurveyData);

  return (
    <>
      <section className={`${pageStyles.section}`}>
        <div className={`container`}>
          <div className={`row ${pageStyles.row}`}>
            <div>Participant's Survey Report</div>
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
                    <tr key={data._id}>
                      <td>{data.code}</td>
                      <td>{data.firstName}</td>
                      <td>{data.lastName}</td>
                      <td>{data.nationality}</td>
                      <td>{data.currentResidence}</td>
                      <td>{data.gender}</td>
                      <td>{data.agreedToTerms}</td>
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