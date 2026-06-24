import { useNavigate } from "react-router-dom";
import { haptic } from "../telegram";
import type { AssistantSearch } from "../types";

interface Props {
  result: AssistantSearch;
  wishQuery?: string;
}

export default function AiMessage({ result, wishQuery }: Props) {
  const navigate = useNavigate();

  const openWish = () => {
    haptic();
    navigate("/orders", { state: { wishTitle: wishQuery || "" } });
  };

  return (
    <div className="ai-message">
      <span className="ai-message-icon">🤖</span>
      <div className="ai-message-body">
        <p>{result.message}</p>
        {result.companion && !result.message.includes(result.companion) && (
          <p className="hint ai-message-companion">{result.companion}</p>
        )}
        {result.action === "create_wish" && (
          <button type="button" className="btn small ai-action-btn" onClick={openWish}>
            Запрос поварам
          </button>
        )}
      </div>
    </div>
  );
}
