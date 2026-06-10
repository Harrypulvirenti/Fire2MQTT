package dev.harrypulvirenti.fire2mqtt.ui

import androidx.annotation.StringRes
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.ui.res.stringResource

/**
 * Text the ViewModel emits without resolving it — either a literal [TextString] or a
 * string-resource reference [TextResource] (+ format args). The UI calls [resolve] to get
 * the actual, locale-correct text at render time, so resource resolution stays out of the
 * ViewModel (which therefore needs no Context for strings).
 */
@Immutable
sealed interface TextValue {

    @Immutable
    data class TextString(val value: String) : TextValue

    /** [args] must hold immutable values (strings, numbers) — never mutated after creation. */
    @Immutable
    data class TextResource(
        @StringRes val resId: Int,
        val args: List<Any> = emptyList(),
    ) : TextValue

    @Composable
    fun resolve(): String = when (this) {
        is TextString -> value
        is TextResource -> stringResource(resId, *args.toTypedArray())
    }
}
