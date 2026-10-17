const DB_NAME = "hps_vectors"
const DB_VERSION = 1
const STORE = "figures"
const META_STORE = "meta"

function openDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION)
    req.onupgradeneeded = e => {
      const db = e.target.result
      if (!db.objectStoreNames.contains(STORE)) db.createObjectStore(STORE, { keyPath: "id" })
      if (!db.objectStoreNames.contains(META_STORE)) db.createObjectStore(META_STORE)
    }
    req.onsuccess = e => resolve(e.target.result)
    req.onerror = e => reject(e.target.error)
  })
}

export async function saveVectors(figures) {
  const db = await openDB()
  const tx = db.transaction([STORE, META_STORE], "readwrite")
  const store = tx.objectStore(STORE)
  const meta = tx.objectStore(META_STORE)
  // Clear first: `put` alone leaves figures deleted on the server in the cache
  // forever, so the map and benchmark keep showing them.
  store.clear()
  for (const f of figures) store.put(f)
  meta.put(Date.now(), "last_updated")
  return new Promise((res, rej) => { tx.oncomplete = res; tx.onerror = rej })
}

export async function loadVectors() {
  const db = await openDB()
  const tx = db.transaction(STORE, "readonly")
  const store = tx.objectStore(STORE)
  return new Promise((res, rej) => {
    const req = store.getAll()
    req.onsuccess = () => res(req.result)
    req.onerror = () => rej(req.error)
  })
}

export async function getLastUpdated() {
  const db = await openDB()
  const tx = db.transaction(META_STORE, "readonly")
  const store = tx.objectStore(META_STORE)
  return new Promise((res, rej) => {
    const req = store.get("last_updated")
    req.onsuccess = () => res(req.result || null)
    req.onerror = () => rej(req.error)
  })
}

export async function clearVectors() {
  const db = await openDB()
  const tx = db.transaction(STORE, "readwrite")
  tx.objectStore(STORE).clear()
  return new Promise((res, rej) => { tx.oncomplete = res; tx.onerror = rej })
}
