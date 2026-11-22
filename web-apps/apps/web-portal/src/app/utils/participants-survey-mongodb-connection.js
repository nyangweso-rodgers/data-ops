import mongoose from "mongoose";
import dotenv from "dotenv";
import path from "path";

// Load the repo-root .env (data-ops/.env); cwd is the app folder when run via pnpm.
// In Docker that file isn't there, so dotenv skips it and container env vars are used.
dotenv.config({ path: path.resolve(process.cwd(), "../../../.env") });

// Cache the connection on globalThis so dev hot reloads and concurrent requests
// share one connection instead of opening a new one per call.
const cache = (globalThis.__participantsSurveyMongo ??= { promise: null });

const connectToMongoDB = async () => {
  // 1 = connected: nothing to do.
  if (mongoose.connection.readyState === 1) return mongoose.connection;
  // 0 = disconnected (e.g. closed elsewhere): drop the stale promise and reconnect.
  if (mongoose.connection.readyState === 0) cache.promise = null;

  // Checked here (not at import) so `next build` doesn't need the variable.
  const uri = process.env.WEB_APPS_MONGODB_URI;
  if (!uri) {
    throw new Error("WEB_APPS_MONGODB_URI is not set (see data-ops/.env)");
  }

  if (!cache.promise) {
    cache.promise = mongoose
      .connect(uri, { serverSelectionTimeoutMS: 5000 })
      .then((m) => {
        // Never log the URI: it contains the password.
        console.log("Participants Survey App connected to MongoDB");
        return m.connection;
      })
      .catch((error) => {
        cache.promise = null; // allow a retry on the next call
        console.error(
          "Participants Survey App failed to connect to MongoDB:",
          error.message
        );
        throw error;
      });
  }
  return cache.promise;
};

export default connectToMongoDB;
