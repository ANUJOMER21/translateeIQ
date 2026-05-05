# Step-by-step: Deploy translateeIQ on Google Cloud (full stack)

This walks you from an empty GCP project to a **single Cloud Run URL** that serves the **React app** and the **Django API** (`/api/...`), plus a **Celery worker** for uploads and processing.

**Time:** first time roughly 45–90 minutes (mostly waiting on Cloud SQL and first Cloud Build).

**You will need:** a Google account, billing enabled on a GCP project, and a terminal with `gcloud` and `openssl` (macOS/Linux have both).

---

## Step 1 — Install and log in to Google Cloud CLI

1. Install the [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) if you do not have it.
2. Log in and pick your project:

```bash
gcloud auth login
gcloud projects list
```

3. Set your **project ID** and **region** (use the same region everywhere below; example uses `us-central1`):

```bash
export GCP_PROJECT_ID="your-actual-project-id"
export GCP_REGION="us-central1"

gcloud config set project "$GCP_PROJECT_ID"
```

---

## Step 2 — Enable required Google APIs

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  sqladmin.googleapis.com
```

Wait until the command finishes with no errors.

---

## Step 3 — Create an Artifact Registry repository (Docker)

Docker images for translateeIQ will be stored here. **Run once per project/region.**

```bash
gcloud artifacts repositories create meeting-transcriber \
  --repository-format=docker \
  --location="$GCP_REGION" \
  --description="translateeIQ images"
```

If it already exists, you will see an error — that is fine; continue.

### Step 3b — IAM: let Cloud Build push images (fix `uploadArtifacts` denied)

Cloud Build must be able to **push** to Artifact Registry. Your logs may show the worker as **`PROJECT_NUMBER-compute@developer.gserviceaccount.com`**; grant roles at **project** level (simplest):

```bash
export GCP_PROJECT_ID="your-actual-project-id"   # e.g. transcriptbackend-495200
PROJECT_NUMBER="$(gcloud projects describe "$GCP_PROJECT_ID" --format='value(projectNumber)')"

CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

for SA in "$CLOUD_BUILD_SA" "$COMPUTE_SA"; do
  gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
    --member="serviceAccount:${SA}" \
    --role="roles/artifactregistry.writer"
done

# So build logs appear in Cloud Logging (optional but recommended)
gcloud projects add-iam-policy-binding "$GCP_PROJECT_ID" \
  --member="serviceAccount:${COMPUTE_SA}" \
  --role="roles/logging.logWriter"
```

If you still see **denied on resource (or it may not exist)**, confirm the repo exists:  
`gcloud artifacts repositories list --location="$GCP_REGION"` — you should see **`meeting-transcriber`** in the same region as your image (`us-central1` in the default scripts).

---

## Step 4 — PostgreSQL (Cloud SQL) for production data

SQLite inside the container is only for quick smoke tests. For real users and data you need Postgres.

**Option A — Google Cloud SQL (typical on GCP)**

1. Open [Cloud SQL instances](https://console.cloud.google.com/sql/instances) → **Create instance** → **PostgreSQL**.
2. Choose instance ID, password for the default user, and region **`us-central1`** (match `GCP_REGION`).
3. After creation, create a **database** (e.g. `translateeIQ`) and note the user/password.
4. Under **Connections**, enable **Public IP** (simplest for first deploy) and add your IP or `0.0.0.0/0` only for testing (tighten later).
5. Build **`DATABASE_URL`** (replace placeholders):

```text
postgres://DB_USER:DB_PASSWORD@CLOUD_SQL_PUBLIC_IP:5432/translateeIQ?sslmode=require
```

**Cloud Run cannot open your database** if the VM/firewall drops Google’s egress. If you see **connection timed out** from Cloud Run migrate logs:

- **Preferred:** In Cloud Run, attach **Cloud SQL** (Console → service → Connections → Cloud SQL → add instance, **or** deploy with `--add-cloudsql-instances PROJECT:REGION:INSTANCE`). Set `DATABASE_URL` to use the Unix socket:

  ```text
  postgresql://DB_USER:DB_PASSWORD@/translateeIQ?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME
  ```

  From the repo root you can deploy with:

  ```bash
  export CLOUDSQL_CONNECTION_NAME="$GCP_PROJECT_ID:us-central1:YOUR_INSTANCE_NAME"
  ```

  alongside `GCP_ENV_FILE=deploy/gcp-run.env.yaml ./deploy/deploy-gcp-cloud-run.sh` (script passes `--add-cloudsql-instances` when this variable is set).

- **If you keep Public IP:** In Cloud SQL → **Networking**, authorized networks cannot list every Cloud Run IP; use **`0.0.0.0/0`** only for short tests, then move to **[static outbound IP via VPC Connector + NAT](https://cloud.google.com/run/docs/configuring/static-outbound-ip)** and whitelist those IPs — or stick with the **Cloud SQL connector** above.

**Option B — External Postgres (Neon, Supabase, etc.)**

Use the connection string they provide; ensure it includes TLS if required (`sslmode=require`).

---

## Step 5 — Redis for Celery (required for uploads/processing)

Cloud Run does not provide Redis. Use a managed Redis with TLS, for example **[Upstash](https://upstash.com/)**:

1. Create a Redis database in the same region as Cloud Run if possible.
2. Copy the **rediss://** URL (TLS). You will use it for **both** `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`.

Example shape (not real credentials):

```text
rediss://default:YOUR_PASSWORD@YOUR_HOST:6379
```

---

## Step 6 — Anthropic API key (AI features)

translateeIQ uses **Anthropic** for agents and chat. In [Anthropic Console](https://console.anthropic.com/) create an API key.

If you skip this, some features will fail in production; you can still test the shell with `TRANSCRIPTION_BACKEND=mock`.

---

## Step 7 — Create your Cloud Run env file

1. On your machine, go to the **repository root** (the folder that contains `Dockerfile` and `package.json`).

2. Copy the example file:

```bash
cp deploy/gcp-run.env.yaml.example deploy/gcp-run.env.yaml
```

3. Edit **`deploy/gcp-run.env.yaml`** (never commit it; keep it secret):

| Key | What to put |
|-----|----------------|
| `DJANGO_SECRET_KEY` | Run: `openssl rand -hex 32` and paste the output inside the quotes. |
| `DJANGO_DEBUG` | `"False"` |
| `ALLOWED_HOSTS` | For first test you can use `"*"`. After you know your Cloud Run URL, set it to the hostname only, e.g. `meeting-api-xxxxx-uc.a.run.app` (no `https://`). |
| `SERVE_SPA` | `"1"` (serves the React app from the same service). |
| `TRANSCRIPTION_BACKEND` | `"mock"` on small Cloud Run unless you plan heavy CPU for Whisper. |
| `DATABASE_URL` | Your Postgres URL from Step 4. |
| `CELERY_BROKER_URL` | Your Redis URL from Step 5. |
| `CELERY_RESULT_BACKEND` | Same as broker (or what your provider documents). |
| `ANTHROPIC_API_KEY` | Your key from Step 6. |
| `CORS_ALLOWED_ORIGINS` | Comma-separated, **no spaces**. Include `http://localhost:5173` for local dev. **After first deploy**, add your real UI URL: `https://YOUR-SERVICE-xxxxx.run.app` (same as Cloud Run URL). |
| `CSRF_TRUSTED_ORIGINS` | `https://YOUR-SERVICE-xxxxx.run.app` (used if you use Django admin on that host). |

**Tip:** Deploy once without the perfect `CORS_*` URL, copy the service URL from the script output, then update `gcp-run.env.yaml` and redeploy or run `gcloud run services update` with the new env file.

---

## Step 8 — Deploy the API + frontend (first Cloud Run service)

From the **repository root**:

```bash
chmod +x deploy/deploy-gcp-cloud-run.sh

export GCP_PROJECT_ID="your-actual-project-id"
export GCP_REGION="us-central1"
export GCP_ENV_FILE=deploy/gcp-run.env.yaml

./deploy/deploy-gcp-cloud-run.sh
```

When `GCP_ENV_FILE` is set, the script defaults **`--max-instances 1`** for `meeting-api` so **chunk uploads** stay on one container (filesystem is ephemeral). Raise concurrency with **`CLOUD_RUN_MAX_INSTANCES=5`** (etc.) once you move uploads to shared storage such as **GCS**.

What this does:

1. Uploads the repo to **Cloud Build**.
2. Builds the **root `Dockerfile`** (Vite → static files + Django).
3. Pushes the image to Artifact Registry.
4. Deploys a Cloud Run service (default name **`meeting-api`**).

At the end, the script prints:

- **Service URL** — open this in a browser: you should see **translateeIQ**.
- **Health URL** — `https://.../api/health/` should return JSON like `{"status":"ok"}`.

**Smoke test without Postgres:** omit `GCP_ENV_FILE` once to use ephemeral SQLite (data is lost when the instance recycles). Only for demos.

---

## Step 8b — Shared media for uploads (API + worker)

Chunk files and assembled meetings must be visible to **both** `meeting-api` and `meeting-worker`. Pick **one** approach.

### Option A — `GS_MEDIA_BUCKET` (recommended)

The app uses **django-storages** when **`GS_MEDIA_BUCKET`** is set in `deploy/gcp-run.env.yaml` (no Cloud Run volume mounts).

1. Create a bucket (any name, e.g. `YOUR_PROJECT_ID-meeting-media`), same region as Cloud Run if you like.
2. Grant **`roles/storage.objectAdmin`** on that bucket to the **Cloud Run service account** (often `PROJECT_NUMBER-compute@developer.gserviceaccount.com`). Both `meeting-api` and `meeting-worker` use that identity unless you overrode `--service-account`.
3. Add to **`deploy/gcp-run.env.yaml`**:

   ```yaml
   GS_MEDIA_BUCKET: "YOUR_PROJECT_ID-meeting-media"
   GCP_PROJECT_ID: "YOUR_PROJECT_ID"
   ```

   (`GCP_PROJECT_ID` helps signed playback URLs; Cloud Run also injects metadata, but the explicit env is safe.)

4. **Redeploy** `meeting-api` and `meeting-worker` with the updated env file and a **new image** that includes `django-storages` (see repo `requirements.txt`).

5. If the browser cannot play video from a signed URL, add a [CORS configuration](https://cloud.google.com/storage/docs/configuring-cors) on the bucket allowing `GET` from your app origin.

### Option B — Mount the same bucket at `/app/media` (Step 9b)

Use Cloud Run **bucket volumes** if you prefer not to use `GS_MEDIA_BUCKET`. See **Step 9b** below.

---

## Step 9 — Deploy the Celery worker (second Cloud Run service)

Processing runs in a **worker**, not in the web request. Use the **same image** as the deploy script printed (`Image: ...`).

From the **repository root** (so `deploy/gcp-run.env.yaml` resolves correctly):

```bash
export GCP_PROJECT_ID="your-actual-project-id"
export GCP_REGION="us-central1"

# Paste the tag from the deploy script output (`Image: ...`), then:
export IMAGE_TAG="20260503120000"
export IMAGE="us-central1-docker.pkg.dev/${GCP_PROJECT_ID}/meeting-transcriber/meeting-api:${IMAGE_TAG}"
# If you see `projects/your-project` in an error, you used the docs placeholder — use `GCP_PROJECT_ID` in the image URL (e.g. `transcriptbackend-495200`), not the string `your-project`.

# Required when deploy/gcp-run.env.yaml DATABASE_URL uses Unix socket (?host=/cloudsql/PROJECT:REGION:INSTANCE)
export CLOUDSQL_CONNECTION_NAME="your-project-id:us-central1:your-instance-id"

gcloud run deploy meeting-worker \
  --image "$IMAGE" \
  --region "$GCP_REGION" \
  --no-allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 5 \
  --add-cloudsql-instances "$CLOUDSQL_CONNECTION_NAME" \
  --command ./run-celery-cloud-run.sh \
  --env-vars-file deploy/gcp-run.env.yaml
```

If `DATABASE_URL` is **public IP** only (not recommended for Cloud Run), **remove** **`--add-cloudsql-instances ...`** and **`export CLOUDSQL_CONNECTION_NAME`**, and configure Cloud SQL **Authorized networks** instead.

**Why `./run-celery-cloud-run.sh`:** Cloud Run expects the container to **listen on HTTP port `$PORT`** (default 8080) during startup. A plain Celery worker does not bind that port, so deploy fails. The script starts a minimal listener on **`$PORT`** and then runs the Celery worker (see `backend/run-celery-cloud-run.sh`).

Optional: set **`CELERY_LOG_LEVEL`** (e.g. `DEBUG`) in `gcp-run.env.yaml` to change worker log verbosity.

- **`meeting-worker`** is the service name; change if you prefer.
- The worker does not need public HTTP; `--no-allow-unauthenticated` is normal (nothing should call it from the browser).

### Step 9b — Same media volume on API **and** worker (Option B only)

If you are **not** using **`GS_MEDIA_BUCKET`**: `meeting-api` writes chunk uploads under **`/app/media`**, and **`meeting-worker`** must see the same files. Attach the **same Cloud Storage bucket** to both services (see [Mount Cloud Storage buckets](https://cloud.google.com/run/docs/configure/services/cloud-storage-volume-mounts)).

1. Create a bucket (same region as Cloud Run helps), then grant **`roles/storage.objectAdmin`** on that bucket to the **Cloud Run runtime service accounts** used by **`meeting-api`** and **`meeting-worker`** (often the default compute SA: `PROJECT_NUMBER-compute@developer.gserviceaccount.com`).

2. Mount it at **`/app/media`** on **both** services (adjust `SERVICE` and run twice, or duplicate flags on deploy):

```bash
export MEDIA_BUCKET="${GCP_PROJECT_ID}-meeting-media"   # or your bucket name
export VOL_NAME="media"

for SVC in meeting-api meeting-worker; do
  gcloud run services update "$SVC" \
    --region="$GCP_REGION" \
    --add-volume="name=${VOL_NAME},type=cloud-storage,bucket=${MEDIA_BUCKET}" \
    --add-volume-mount="volume=${VOL_NAME},mount-path=/app/media"
done
```

If the services already have volumes, prefer **`gcloud run services describe`** and the console to add a matching bucket mount rather than stacking duplicate mounts by mistake.

After this, chunked uploads and transcription share the mounted bucket. **`Missing chunk …`** errors from split local disks should stop.

If you use **Option A (`GS_MEDIA_BUCKET`)**, you can skip this volume mount.

---

## Step 10 — Database migrations

The web container **entrypoint** runs `python manage.py migrate` on startup before Gunicorn starts. After you deploy a new image, new migrations apply on the next instance start. You normally do **not** run migrate by hand.

---

## Step 11 — Verify end-to-end

1. Open the **service URL** → translateeIQ UI loads.
2. Open **`/api/health/`** on the same host → OK response.
3. **Register** a user in the app → should hit `POST /api/auth/register/`.
4. **Upload** a small test file → should progress if the **worker** is running and Redis/DB are correct.

If uploads hang at processing, check **worker logs**:

```bash
gcloud run services logs read meeting-worker --region="$GCP_REGION" --limit=50
```

Web service logs:

```bash
gcloud run services logs read meeting-api --region="$GCP_REGION" --limit=50
```

---

## Step 12 — Tighten security (after everything works)

1. Set **`ALLOWED_HOSTS`** to your exact Cloud Run hostname (remove `*`).
2. Set **`CORS_ALLOWED_ORIGINS`** and **`CSRF_TRUSTED_ORIGINS`** to your real `https://...run.app` (and localhost only if you still need local dev against prod).
3. Restrict Cloud SQL to **private IP** or a small set of authorized networks instead of `0.0.0.0/0`.
4. Store secrets in **Secret Manager** and reference them from Cloud Run (optional upgrade from a plain env file).

---

## Quick reference — important paths

| What | Where |
|------|--------|
| Full-stack Dockerfile | Repo root `Dockerfile` |
| Deploy script | `deploy/deploy-gcp-cloud-run.sh` |
| Env template | `deploy/gcp-run.env.yaml.example` → copy to `deploy/gcp-run.env.yaml` |
| Deep reference (auth, env table, troubleshooting) | `deploy/SETUP.md` |

---

## Common problems

| Symptom | What to check |
|---------|----------------|
| CORS errors in browser | `CORS_ALLOWED_ORIGINS` must include the exact origin (`https://your-host.run.app`, no trailing slash). |
| 502 on large upload | Increase Cloud Run **memory** and **request timeout** for `meeting-api`. |
| Processing never finishes | Worker not deployed, wrong `CELERY_*` URLs, or worker cannot reach Redis/Postgres. |
| Blank page or 404 on refresh | Ensure `SERVE_SPA=1` and you deployed the **root** image (repo context), not API-only. |
| Database connection errors | `DATABASE_URL`, SSL mode, Cloud SQL authorized networks, or connector configuration. |
| **`migrate` timeouts / Postgres unreachable from Cloud Run** | DB only allows a private network or IPs that exclude Cloud Run. Use **Unix socket `DATABASE_URL` + `--add-cloudsql-instances`** (see Step 4) or widen authorized networks temporarily. |
| **`redis … localhost:6379` / upload complete → 500** | Serving revision missing **`CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND`**, or SQLite smoke revision while Postgres deploy failed. Deploy a healthy revision that includes **`gcp-run.env.yaml`**. The app now **refuses boot** if `DATABASE_URL` is set without Celery URLs. |
| **`ImproperlyConfigured` about Celery** | Either set **`CELERY_BROKER_URL`** and **`CELERY_RESULT_BACKEND`** whenever **`DATABASE_URL`** is set, or use **`CELERY_TASK_ALWAYS_EAGER=True`** only for non-production debugging. |
| `gcloud builds submit` **NOT_FOUND** | Create the **Artifact Registry** repo once: `gcloud artifacts repositories create meeting-transcriber --repository-format=docker --location=us-central1 --description=translateeIQ`. Enable **Artifact Registry API**: `gcloud services enable artifactregistry.googleapis.com`. Confirm billing is on for the project. |
| Cloud Build uploads **gigabytes** / tens of thousands of files | The repo must include **`.gcloudignore`** (and usually **`.gitignore`**) so `node_modules`, Python venvs, and `backend/media` are **not** uploaded. `gcloud` does not use `.dockerignore` for the upload step. |
| **`storage.objects.get` denied** / `…-compute@developer.gserviceaccount.com` **403** on `_cloudbuild` bucket | Cloud Build must read the uploaded tarball. Run the IAM fix in **deploy/FIX-CLOUD-BUILD-GCS.md** (grant **Cloud Build SA** + **Compute default SA** `roles/storage.objectViewer` on `gs://PROJECT_ID_cloudbuild`, or project-level **Storage Admin** for Cloud Build SA). |
| **`artifactregistry.repositories.uploadArtifacts` denied** / push retries exhausted | Grant **`roles/artifactregistry.writer`** to **`PROJECT_NUMBER@cloudbuild.gserviceaccount.com`** and **`PROJECT_NUMBER-compute@developer.gserviceaccount.com`** on the project (see **Step 3b**). Confirm the **Artifact Registry** repo name and region match `deploy/deploy-gcp-cloud-run.sh` (`meeting-transcriber` in `us-central1` by default). |
| **`downloadArtifacts` denied**; error shows `projects/your-project/...` | The image URL still used the docs placeholder **`your-project`**. Use your real project ID, e.g. `us-central1-docker.pkg.dev/transcriptbackend-495200/meeting-transcriber/meeting-api:TAG` (see **Step 9**). If the project ID in the URL is already correct, grant **`roles/artifactregistry.reader`** on that repo to the account deploying and ensure the **Cloud Run service account** can pull (same project is usually automatic). |
| **Worker deploy:** `failed to start and listen on the port ... PORT=8080` | Cloud Run requires an HTTP listener on **`$PORT`**. Deploy the worker with **`--command ./run-celery-cloud-run.sh`** (not raw `celery ...`). Rebuild the image so it includes `backend/run-celery-cloud-run.sh` and `backend/cloud_run_port_health.py`. |
| **`A rediss:// URL must have parameter ssl_cert_reqs`** | Celery 5.x requires **`ssl_cert_reqs`** on Upstash **`rediss://`** URLs; the backend patches env variables before Django/Celery start. **Rebuild the Docker image**, redeploy **both** `meeting-api` and `meeting-worker` with current code. You can also append **`?ssl_cert_reqs=CERT_REQUIRED`** to **`CELERY_BROKER_URL`** / **`CELERY_RESULT_BACKEND`** in `gcp-run.env.yaml`; if TLS verification fails against Upstash, **`CERT_NONE`** is only for narrowing down connectivity problems. |
| **`Missing chunk …` / assembly **`FileNotFoundError`** | **`meeting-api`** and **`meeting-worker`** do not share local disk. Set **`GS_MEDIA_BUCKET`** in `gcp-run.env.yaml` (**Step 8b**, recommended) **or** mount the same bucket at **`/app/media`** on both services (**Step 9b**). Redeploy both services with a current image. |
| **Logs Writer** / build logs incomplete for compute SA | Grant **`roles/logging.logWriter`** to **`PROJECT_NUMBER-compute@developer.gserviceaccount.com`** (see **Step 3b**). |

---

You are done when the UI loads on Cloud Run, health passes, and a test upload completes with the worker logs showing task progress.
