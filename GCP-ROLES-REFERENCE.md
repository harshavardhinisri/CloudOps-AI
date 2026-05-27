# GCP Roles - How to Find and Add Them

If you can't find the exact role names, use these **official role IDs** instead.

## Step-by-Step to Add Roles (Corrected)

1. Go to **IAM & Admin** → **Service Accounts**
2. Click your service account (`cloudops-ai-app`)
3. Go to **"PERMISSIONS"** tab
4. Click **"GRANT ACCESS"** button
5. Paste your service account email in "New principals"
6. In the **"Select a role"** dropdown, search for each role below

## Exact Role Names (Copy-Paste These)

When you click the role dropdown, search for:

### For Vertex AI
Search for: `aiplatform.user`
Or scroll to find: **"Vertex AI User"**

### For Firestore/Datastore
Search for: `datastore.user`
Or scroll to find: **"Cloud Datastore User"**

### For Pub/Sub
Search for: `pubsub.editor`
Or scroll to find: **"Pub/Sub Editor"**

### For Cloud Logging
Search for: `logging.logWriter`
Or scroll to find: **"Cloud Logging Writer"**

---

## Alternative: Use Basic Roles (Easier)

If you still can't find them, use these **basic roles** (less secure but works for demo):

1. Click role dropdown
2. Search for: `editor`
3. Select: **"Editor"** (gives all permissions)
4. Click **"ADD ANOTHER ROLE"**
5. Do this 1-2 times if needed

**⚠️ Note:** "Editor" role is overkill for demo but easier to find.

---

## Visual Guide

The dropdown shows roles like this:

```
Search box at top: [________________]

Results:
  ☐ Vertex AI User
  ☐ Cloud Datastore User
  ☐ Pub/Sub Editor
  ☐ Cloud Logging Writer
  ☐ Editor (basic role)
  ☐ Viewer (basic role)
  ... and more
```

Just **type in the search box** to find them faster!

---

## If Still Not Found

Try these role IDs directly (paste in search):

- `roles/aiplatform.user`
- `roles/datastore.user`
- `roles/pubsub.editor`
- `roles/logging.logWriter`

---

## Quick Solution for Demo

Just add **"Editor"** role:
1. Dropdown → Search "editor" → Select "Editor"
2. Click "SAVE"
3. Done! (Works for demo purposes)

Then continue with Cloud Run deployment.

