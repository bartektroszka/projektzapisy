/**
 * @file Theses app permission checks, mostly analogous to permissions.py
 */
import { ThesisStatus } from "./protocol_types";
import { Thesis } from "./thesis";
import { Users } from "./app_logic/users";

/**
 * Determine whether the current app user is permitted to add new thesis objects
 */
export function canAddThesis() {
	return !Users.isUserStudent();
}

/**
 * Determine whether the current user "owns" the specified thesis
 * @param thesis The thesis
 */
function isOwnerOfThesis(thesis: Thesis): boolean {
	return !!thesis.advisor && thesis.advisor.isEqual(Users.currentUser.person);
}

/**
 * Determine if the current user is permitted to make any changes to the specified thesis
 * @param thesis The thesis
 */
export function canModifyThesis(thesis: Thesis) {
	if (thesis.isArchived()) {
		return Users.isUserAdmin();
	}
	return Users.isUserStaff() || isOwnerOfThesis(thesis);
}

// The functions below will only be used if the one above returns true,
// so they don't need to repeat their checks

/**
 * Determine if the specified user is permitted to change the title of the specified thesis
 * @param thesis The thesis
 */
export function canChangeTitle(thesis: Thesis) {
	const allowedStatuses = [
		ThesisStatus.BeingEvaluated, ThesisStatus.ReturnedForCorrections,
	];
	return (
		Users.isUserStaff() ||
		isOwnerOfThesis(thesis) && allowedStatuses.includes(thesis.status)
	);
}

/**
 * Determine if a user of the specified type can modify an existing thesis' status
 */
export function canChangeStatus() {
	return Users.isUserStaff();
}

/**
 * Determine if the specified user is allowed to set any advisor on any thesis
 */
export function canSetArbitraryAdvisor() {
	return Users.isUserStaff();
}