import Link from "next/link";
import errorStyles from "../../styles/error.module.css";

const ErrorPage = () => {
  return (
    <>
      <head>
        <title>Oops! Page not found</title>
      </head>
      <main className={`${errorStyles.errorContainer}`}>
        <h1>404</h1>
        <p>Opps! This page is lost in space.</p>
        <Link href="/" className={`btn`}>
          Return home
        </Link>
      </main>
    </>
  );
};

export default ErrorPage;
