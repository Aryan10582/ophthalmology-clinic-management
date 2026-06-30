# Ophthalmology Clinic Frontend

Responsive Next.js frontend for the doctor consultation module.

## Run

```bash
cp .env.example .env.local
pnpm install --config.confirmModulesPurge=false
pnpm run dev --hostname 127.0.0.1 --port 3000
```

Open http://localhost:3000 and log in with a seeded doctor or receptionist account.

Doctor demo:

- Email: `rupa.kapale@clinic.com`
- Password: `Doctor@12345`

Receptionist demo:

- Email: `reception1@clinic.com`
- Password: `Reception@12345`

## Screens

- `/dashboard`
- `/patients`
- `/patients/[id]`
- `/consultations/new`
- `/consultations/[id]`
- `/consultations/[id]/edit`
- `/queue`
- `/operations`
- `/operations/[id]`
- `/calendar`

## Verification

```bash
pnpm run typecheck
pnpm run build
```
