import LoadingBar from "@cloudscape-design/chat-components/loading-bar";
import Box from "@cloudscape-design/components/box";
import Alert from "@cloudscape-design/components/alert";

export const FormLoadingBar = () => {
  return (
    <Alert type={"info"}>
      <Box
        margin={{ bottom: "xs" }}
        color="text-body-secondary"
      >
        Generating a response
      </Box>
      <LoadingBar variant="gen-ai" />
    </Alert>
  );
}