import * as React from "react";

export const enum InputType {
	Normal,
	ReadOnly,
	Disabled,
}

type Props = {
	labelText: string;
	inputText: string;
	inputType: InputType,
};

export function InputWithLabel(props: Props) {
	return <table>
		<tbody>
			<tr>
				<td style={{ paddingRight: "5px" }}>
					<span>{props.labelText}</span>
				</td>
				<td>
				<input
					type={"text"}
					value={props.inputText}
					readOnly={props.inputType === InputType.ReadOnly}
					disabled={props.inputType === InputType.Disabled}
				/>
				</td>
			</tr>
		</tbody>
	</table>;
}