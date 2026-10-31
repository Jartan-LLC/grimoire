export const COURSES = ["starter", "main", "side", "dessert", "drinks"];

/**
 * Adds a guest's dish to the sheet and returns the new sheet; the sheet passed in is not changed.
 * @param {{ guests: { name: string, dish: string, course: string }[] }} sheet
 * @param {{ name: string, dish: string, course: string }} signup
 */
export function signUp(sheet, signup) {
  if (!COURSES.includes(signup.course)) {
    throw new Error(`unknown course: ${signup.course}`);
  }
  if (sheet.guests.some((guest) => guest.name === signup.name)) {
    throw new Error(`${signup.name} has already signed up`);
  }
  return { ...sheet, guests: [...sheet.guests, signup] };
}

/** Removes a guest's sign-up; an unknown name leaves the sheet as it is. */
export function cancel(sheet, name) {
  return { ...sheet, guests: sheet.guests.filter((guest) => guest.name !== name) };
}
