import { COURSES } from "./signup.js";

/** The number of dishes per course, every course listed. */
export function courseCounts(sheet) {
  const counts = Object.fromEntries(COURSES.map((course) => [course, 0]));
  for (const guest of sheet.guests) {
    counts[guest.course] += 1;
  }
  return counts;
}

/** The courses nobody has signed up for yet, in menu order. */
export function missingCourses(sheet) {
  const counts = courseCounts(sheet);
  return COURSES.filter((course) => counts[course] === 0);
}
