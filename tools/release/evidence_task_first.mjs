// Task-First UX (31 Oct 2026): the Project page (/projects/<id>) keeps each part of the job in a closed section, and
// More actions closed. Before a walk reads or uses something on it, it opens them, as a person opens the section
// they need. Kept apart from evidence_common.mjs, whose bytes are pinned (tests/test_release_tools.py).
export const PROJECT_PAGE = /^\/projects\/\d+\/?$/;
export async function openSections(pg) {
  await pg.evaluate(() => document.querySelectorAll("details[data-ts-section], details[data-more-actions]")
    .forEach((d) => { d.open = true; }));
}
export async function openSectionsIfProjectPage(pg) {
  if (PROJECT_PAGE.test(new URL(pg.url()).pathname)) await openSections(pg);
}
