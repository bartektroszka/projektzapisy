import * as React from "react";
import "react-select/dist/react-select.css";
import styled from "styled-components";
import AsyncPaginate from "react-select-async-paginate";

import { getPersonAutocomplete, PersonType } from "../../../backend_callers";
import { BasePerson } from "../../../types";
import { ReadOnlyInput } from "./ReadOnlyInput";

const PersonFieldWrapper = styled.div`
width: 50%;
display: inline-block;
`;

export type PersonSelectOptions = {
	value: string;
	label: string;
};

function personToSelectOptions(person: BasePerson | null): PersonSelectOptions | null {
	return person ? {
		value: String(person.id),
		label: person.displayName,
	} : null;
}

function selectOptionsToPerson(options: PersonSelectOptions | null): BasePerson | null {
	return options ? new BasePerson(
		Number(options.value),
		options.label,
	) : null;
}

class AsyncSelectAutocompleteGetter {
	private personType: PersonType;
	private pageNumberForInput: Map<string, number> = new Map();

	public constructor(personType: PersonType) {
		this.personType = personType;
	}

	public get = async (inputValue: string, _: any) => {
		const thisPageNum = this.pageNumberForInput.get(inputValue) || 1;

		try {
			const acResults = await getPersonAutocomplete(this.personType, inputValue, thisPageNum);
			const result = acResults.results.map(pac => ({ value: pac.id, label: pac.displayName }));

			this.pageNumberForInput.set(inputValue, thisPageNum + 1);

			return {
				options: result,
				hasMore: acResults.hasMore,
				page: thisPageNum,
			};
		} catch (err) {
			alert(`Nie udało się pobrać listy (${err.toString()}); odśwież stronę lub spróbuj później`);
		}
	}
}

type Props = {
	value: BasePerson | null;
	onChange: (newValue: BasePerson | null) => void;
	personType: PersonType;
	readOnly?: boolean;
};

export function PersonField(props: Props) {
	const isReadOnly = typeof props.readOnly !== "undefined" ? props.readOnly : false;
	const valueComponent = isReadOnly
		? <ReadOnlyInput
			text={props.value ? props.value.displayName : "<brak>"}
			style={{ height: "36px", width: "100%", boxSizing: "border-box" }}
		/>
		: <AsyncPaginate
			cacheOptions
			defaultOptions
			loadOptions={(new AsyncSelectAutocompleteGetter(props.personType)).get}
			onChange={(nv: PersonSelectOptions | null) => props.onChange(selectOptionsToPerson(nv))}
			value={personToSelectOptions(props.value)}
			placeholder={"Wybierz..."}
			noResultsText={"Pobieranie listy..."}
		/>;

	return <PersonFieldWrapper>{valueComponent}</PersonFieldWrapper>;
}