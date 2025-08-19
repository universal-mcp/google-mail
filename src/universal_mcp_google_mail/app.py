import base64
from email.message import EmailMessage
from typing import Any
from loguru import logger
import concurrent.futures

from universal_mcp.applications import APIApplication
from universal_mcp.integrations import Integration



class GoogleMailApp(APIApplication):
    def __init__(self, integration: Integration) -> None:
        super().__init__(name="google-mail", integration=integration)
        self.base_api_url = "https://gmail.googleapis.com/gmail/v1/users/me"
        self.base_url = "https://gmail.googleapis.com"

    def send_email(self, to: str, subject: str, body: str, body_type: str = "plain", thread_id: str | None = None) -> dict[str, Any]:
        """
        Sends an email using the Gmail API and returns a confirmation or error message.

        Args:
            to: The email address of the recipient
            subject: The subject line of the email
            body: The content of the email message
            body_type: The MIME subtype for the body ("plain" or "html"). Defaults to "plain".
            thread_id: Optional thread ID to make this a reply to an existing conversation

        Returns:
            A string containing either a success confirmation message or an error description

        Raises:
            NotAuthorizedError: When Gmail API authentication is not valid or has expired
            KeyError: When required configuration keys are missing
            Exception: For any other unexpected errors during the email sending process

        Tags:
            send, email, api, communication, important, thread, reply, openWorldHint
        """

        
        url = f"{self.base_api_url}/messages/send"
        raw_message = self._create_message(to, subject, body, body_type)
        email_data = {"raw": raw_message}
        
        # Add threadId to make it a proper reply if thread_id is provided
        if thread_id:
            email_data["threadId"] = thread_id
            
        response = self._post(url, email_data)

        return self._handle_response(response)



    def _create_message(self, to, subject, body, body_type="plain"):
        try:
            message = EmailMessage()
            message["to"] = to
            message["subject"] = subject
            message["from"] = "me"
            message.set_content(body, subtype=body_type)
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            return raw
        except Exception as e:
            logger.error(f"Error creating message: {str(e)}")
            raise

    def create_draft(self, to: str, subject: str, body: str, body_type: str = "plain", thread_id: str | None = None) -> dict[str, Any]:
        """
        Creates a draft email message in Gmail using the Gmail API and returns a confirmation status.

        Args:
            to: The email address of the recipient
            subject: The subject line of the draft email
            body: The main content/message of the draft email
            body_type: The MIME subtype for the body ("plain" or "html"). Defaults to "plain".
            thread_id: Optional thread ID to make this draft a reply to an existing conversation

        Returns:
            A string containing either a success message with the draft ID or an error message describing the failure

        Raises:
            NotAuthorizedError: When the user's Gmail API authorization is invalid or expired
            KeyError: When required configuration keys are missing
            Exception: For general API errors, network issues, or other unexpected problems

        Tags:
            create, email, draft, gmail, api, important, thread, reply, html
        """
        
        url = f"{self.base_api_url}/drafts"

        raw_message = self._create_message(to, subject, body, body_type)

        draft_data = {"message": {"raw": raw_message}}
        
        # Add threadId to make it a proper reply if thread_id is provided
        if thread_id:
            draft_data["message"]["threadId"] = thread_id

        logger.info(f"Creating draft email to {to}")

        response = self._post(url, draft_data)

        return self._handle_response(response)

    def send_draft(self, draft_id: str) -> dict[str, Any]:
        """
        Sends an existing draft email using the Gmail API and returns a confirmation message.

        Args:
            draft_id: The unique identifier of the Gmail draft to be sent

        Returns:
            A string containing either a success message with the sent message ID or an error message detailing the failure reason

        Raises:
            NotAuthorizedError: When the user's Gmail API authorization is invalid or expired
            KeyError: When required configuration keys are missing from the API response
            Exception: For other unexpected errors during the API request or response handling

        Tags:
            send, email, api, communication, important, draft
        """
        
        url = f"{self.base_api_url}/drafts/send"

        draft_data = {"id": draft_id}

        logger.info(f"Sending draft email with ID: {draft_id}")

        response = self._post(url, draft_data)

        return self._handle_response(response)

    def get_draft(self, draft_id: str, format: str = "full") -> dict[str, Any]:
        """
        Retrieves and formats a specific draft email from Gmail by its ID

        Args:
            draft_id: String identifier of the draft email to retrieve
            format: Output format of the draft (options: minimal, full, raw, metadata). Defaults to 'full'

        Returns:
            A formatted string containing the draft email details (ID, recipient, subject) or an error message if retrieval fails

        Raises:
            NotAuthorizedError: When the user's Gmail authorization is invalid or expired
            KeyError: When required configuration keys or response data fields are missing
            Exception: For any other unexpected errors during draft retrieval

        Tags:
            retrieve, email, gmail, draft, api, format, important
        """
        
        url = f"{self.base_api_url}/drafts/{draft_id}"

            # Add format parameter as query param
        params = {"format": format}

        logger.info(f"Retrieving draft with ID: {draft_id}")

        response = self._get(url, params=params)

        return self._handle_response(response)

       

    def list_drafts(
        self, max_results: int = 20, q: str | None = None, include_spam_trash: bool = False
    ) -> dict[str, Any]:
        """
        Retrieves and formats a list of email drafts from the user's Gmail mailbox with optional filtering and pagination.

        Args:
            max_results: Maximum number of drafts to return (max 500, default 20)
            q: Search query string to filter drafts using Gmail search syntax (default None)
            include_spam_trash: Boolean flag to include drafts from spam and trash folders (default False)

        Returns:
            A formatted string containing the list of draft IDs and count information, or an error message if the request fails

        Raises:
            NotAuthorizedError: When the Gmail API authentication is missing or invalid
            KeyError: When required configuration keys are missing
            Exception: For general errors during API communication or data processing

        Tags:
            list, email, drafts, gmail, api, search, query, pagination, important
        """
        
        url = f"{self.base_api_url}/drafts"

            # Build query parameters
        params: dict[str, Any] = {"maxResults": max_results}

        if q:
                params["q"] = q

        if include_spam_trash:
                params["includeSpamTrash"] = "true"

        logger.info(f"Retrieving drafts list with params: {params}")

        response = self._get(url, params=params)

        return self._handle_response(response)


    def get_message(self, message_id: str) -> dict[str, Any]:
        """
        Retrieves and formats a specific email message from Gmail API by its ID, including sender, recipient, date, subject, and full message body content.

        Args:
            message_id: The unique identifier of the Gmail message to retrieve

        Returns:
            A dictionary containing the cleaned message details (serializable as JSON)

        Tags:
            retrieve, email, format, api, gmail, message, important, body, content
        """
        url = f"{self.base_api_url}/messages/{message_id}"
        response = self._get(url)
        raw_data = self._handle_response(response)

        # Extract headers
        headers = {}
        for header in raw_data.get("payload", {}).get("headers", []):
            name = header.get("name", "")
            value = header.get("value", "")
            headers[name] = value

        # Extract body content
        body_content = self._extract_email_body(raw_data.get("payload", {}))
        if not body_content:
            if "snippet" in raw_data:
                body_content = f"Preview: {raw_data['snippet']}"
            else:
                body_content = "No content available"

        return{
            "message_id":message_id,
            "from_addr":headers.get("From", "Unknown sender"),
            "to":headers.get("To", "Unknown recipient"),
            "date":headers.get("Date", "Unknown date"),
            "subject":headers.get("Subject", "No subject"),
            "body_content":body_content,
            "thread_id":raw_data.get("threadId"),
        }


    def _extract_email_body(self, payload):
        """
        Extracts the email body content from the Gmail API payload.
        
        Args:
            payload: The payload section from Gmail API response
            
        Returns:
            str: The email body content (plain text preferred, HTML as fallback)
        """
        try:
            # Handle single part message
            if payload.get("body") and payload.get("body", {}).get("data"):
                return self._decode_base64(payload["body"]["data"])
            
            # Handle multipart message
            parts = payload.get("parts", [])
            if not parts:
                return ""
            
            plain_text_body = ""
            html_body = ""
            
            for part in parts:
                mime_type = part.get("mimeType", "")
                
                # Extract plain text
                if mime_type == "text/plain":
                    if part.get("body") and part.get("body", {}).get("data"):
                        plain_text_body = self._decode_base64(part["body"]["data"])
                
                # Extract HTML content
                elif mime_type == "text/html":
                    if part.get("body") and part.get("body", {}).get("data"):
                        html_body = self._decode_base64(part["body"]["data"])
                
                # Handle nested multipart (recursive)
                elif mime_type.startswith("multipart/") and part.get("parts"):
                    nested_body = self._extract_email_body(part)
                    if nested_body and not plain_text_body:
                        plain_text_body = nested_body
            
            # Prefer plain text, fallback to HTML
            if plain_text_body:
                return plain_text_body
            elif html_body:
                return f"[HTML Content]\n{html_body}"
            
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting email body: {str(e)}")
            return ""
    
    def _decode_base64(self, data):
        """
        Decodes base64 URL-safe encoded data from Gmail API.
        
        Args:
            data: Base64 URL-safe encoded string
            
        Returns:
            str: Decoded string content
        """
        try:
            # Gmail API uses URL-safe base64 encoding
            decoded_bytes = base64.urlsafe_b64decode(data)
            return decoded_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Error decoding base64 data: {str(e)}")
            return f"[Unable to decode content: {str(e)}]"

    def list_messages(
        self, max_results: int = 10, q: str | None = None, include_spam_trash: bool = False, page_token: str | None = None
    ) ->dict[str, Any]:
        """
        Retrieves and formats a list of messages from the user's Gmail mailbox with optional filtering and pagination support.

        Args:
            max_results: Maximum number of messages to return (max 500, default 20)
            q: Search query string to filter messages using Gmail search syntax.
                Examples:
                    - 'newer_than:1h' for emails from the last hour
                    - 'newer_than:1d' for emails from the last day
                    - 'newer_than:1w' for emails from the last week
                    - 'newer_than:1m' for emails from the last month
                    - 'newer_than:1y' for emails from the last year
                    - 'older_than:1h' for emails from the last hour
                    - 'older_than:1d' for emails from the last day
                    - 'older_than:1w' for emails from the last week
                    - 'older_than:1m' for emails from the last month
                    - 'older_than:1y' for emails from the last year
                    - 'after:2025/07/15 before:2025/07/18' for emails from July 15th to July 18th, 2025
                    - 'from:someone@example.com' for emails from a specific sender
                    - 'subject:invoice' for emails with 'invoice' in the subject
                    - 'has:attachment' for emails with attachments
                    - 'is:unread' for unread emails
            include_spam_trash: Boolean flag to include messages from spam and trash folders (default False)

        Returns:
            A dictionary containing the list of messages and next page token for pagination

        Raises:
            NotAuthorizedError: When the Gmail API authentication is invalid or missing
            KeyError: When required configuration keys are missing
            Exception: For general API errors, network issues, or other unexpected problems

        Tags:
            list, messages, gmail, search, query, pagination, important
        """
        url = f"{self.base_api_url}/messages?format=metadata"

        # Build query parameters
        params: dict[str, Any] = {"maxResults": max_results}

        if q:
            params["q"] = q

        if include_spam_trash:
            params["includeSpamTrash"] = "true"
            
        if page_token:
            params["pageToken"] = page_token

        logger.info(f"Retrieving messages list with params: {params}")

        response = self._get(url, params=params)
        data = self._handle_response(response)
        
        # Extract message IDs
        messages = data.get("messages", [])
        message_ids = [msg.get("id") for msg in messages if msg.get("id")]
        
        # Use ThreadPoolExecutor to get detailed information for each message in parallel
        detailed_messages = []
        if message_ids:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                # Submit all get_message calls
                future_to_message_id = {
                    executor.submit(self.get_message, message_id): message_id 
                    for message_id in message_ids
                }
                
                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_message_id):
                    message_id = future_to_message_id[future]
                    try:
                        result = future.result()
                        detailed_messages.append(result)
                    except Exception as e:
                        logger.error(f"Error retrieving message {message_id}: {str(e)}")
                        # Skip failed messages rather than including error strings
        
        return {
            "messages": detailed_messages,
            "next_page_token": data.get("nextPageToken")
        }

    def get_thread(self, thread_id: str) -> dict[str, Any]:
        """
        Retrieves a specific thread and all its messages from Gmail API.

        Args:
            thread_id: The unique identifier of the Gmail thread to retrieve

        Returns:
            A dictionary containing the thread details and all messages in the thread

        Raises:
            NotAuthorizedError: When Gmail API authentication is invalid or missing
            KeyError: When required configuration keys are missing
            Exception: For general errors during API communication or data processing

        Tags:
            retrieve, email, thread, gmail, api, conversation, important, readOnlyHint, openWorldHint
        """
        url = f"{self.base_api_url}/threads/{thread_id}"
        logger.info(f"Retrieving thread {thread_id}")
        response = self._get(url)
        return self._handle_response(response)

    def list_labels(self) -> dict[str, Any]:
        """
        Retrieves and formats a list of all labels (both system and user-created) from the user's Gmail account, organizing them by type and sorting them alphabetically.

        Args:
            None: This method takes no arguments

        Returns:
            A formatted string containing a list of Gmail labels categorized by type (system and user), with their IDs, or an error message if the operation fails.

        Raises:
            NotAuthorizedError: Raised when the user's Gmail authorization is invalid or missing
            Exception: Raised when any other unexpected error occurs during the API request or data processing

        Tags:
            list, gmail, labels, fetch, organize, important, management
        """
        
        url = f"{self.base_api_url}/labels"

        logger.info("Retrieving Gmail labels")

        response = self._get(url)

        return self._handle_response(response)

    def create_label(self, name: str) -> dict[str, Any]:
        """
        Creates a new Gmail label with specified visibility settings and returns creation status details.

        Args:
            name: The display name of the label to create

        Returns:
            A formatted string containing the creation status, including the new label's name and ID if successful, or an error message if the creation fails

        Raises:
            NotAuthorizedError: Raised when the request lacks proper Gmail API authorization
            Exception: Raised for any other unexpected errors during label creation

        Tags:
            create, label, gmail, management, important
        """

        url = f"{self.base_api_url}/labels"

            # Create the label data with just the essential fields
        label_data = {
                "name": name,
                "labelListVisibility": "labelShow",  # Show in label list
                "messageListVisibility": "show",  # Show in message list
            }

        logger.info(f"Creating new Gmail label: {name}")

        response = self._post(url, label_data)

        return self._handle_response(response)

    def get_profile(self) -> dict[str, Any]:
        """
        Retrieves and formats the user's Gmail profile information including email address, message count, thread count, and history ID.

        Args:
            None: This method takes no arguments besides self

        Returns:
            A formatted string containing the user's Gmail profile information or an error message if the request fails

        Raises:
            NotAuthorizedError: Raised when the user's credentials are invalid or authorization is required
            Exception: Raised for any other unexpected errors during the API request or data processing

        Tags:
            fetch, profile, gmail, user-info, api-request, important
        """
        
        url = f"{self.base_api_url}/profile"

        logger.info("Retrieving Gmail user profile")

        response = self._get(url)
        return self._handle_response(response)




    def update_drafts(self, userId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, message=None) -> dict[str, Any]:
        """
        Updates an existing Gmail draft with new message content and metadata.

        Args:
            userId (string): userId
            id (string): id
            access_token (string): OAuth access token. Example: '{{access_token}}'.
            alt (string): Data format for response. Example: '{{alt}}'.
            callback (string): JSONP Example: '{{callback}}'.
            fields (string): Selector specifying which fields to include in a partial response. Example: '{{fields}}'.
            key (string): API key. Your API key identifies your project and provides you with API access, quota, and reports. Required unless you provide an OAuth 2.0 token. Example: '{{key}}'.
            oauth_token (string): OAuth 2.0 token for the current user. Example: '{{oauth_token}}'.
            prettyPrint (string): Returns response with indentations and line breaks. Example: '{{prettyPrint}}'.
            quotaUser (string): Available to use for quota purposes for server-side applications. Can be any arbitrary string assigned to a user, but should not exceed 40 characters. Example: '{{quotaUser}}'.
            upload_protocol (string): Upload protocol for media (e.g. "raw", "multipart"). Example: '{{upload_protocol}}'.
            uploadType (string): Legacy upload protocol for media (e.g. "media", "multipart"). Example: '{{uploadType}}'.
            xgafv (string): V1 error format. Example: '{{$.xgafv}}'.
            message (object): message
                Example:
                ```json
                {
                  "id": "elit Lorem",
                  "message": {
                    "historyId": "ullamco",
                    "id": "elit",
                    "internalDate": "dolor ullamco elit fugiat",
                    "labelIds": [
                      "incididunt et non cupidatat",
                      "laboris deserunt do nostrud"
                    ],
                    "payload": {
                      "body": {
                        "attachmentId": "irure",
                        "data": "officia laboris",
                        "size": -58003592
                      },
                      "filename": "laboris ad",
                      "headers": [
                        {
                          "name": "labore aute nisi",
                          "value": "reprehenderit esse ex elit"
                        },
                        {
                          "name": "sed",
                          "value": "anim ut veniam elit"
                        }
                      ],
                      "mimeType": "enim quis dolor aliqua veniam",
                      "partId": "consequat ipsum qui",
                      "parts": [
                        {
                          "value": "<Circular reference to #/components/schemas/MessagePart detected>"
                        },
                        {
                          "value": "<Circular reference to #/components/schemas/MessagePart detected>"
                        }
                      ]
                    },
                    "raw": "in enim sit pariatur",
                    "sizeEstimate": -74092231,
                    "snippet": "nostrud in",
                    "threadId": "enim ut ut fugiat"
                  }
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            Drafts
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if id is None:
            raise ValueError("Missing required parameter 'id'")
        request_body = {
            'id': id,
            'message': message,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/drafts/{id}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._put(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()



    def trash_messsages(self, userId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Moves a message to the trash folder (acts like delete functionality).

        Args:
            userId (string): userId
            id (string): id
            access_token (string): OAuth access token. Example: '{{access_token}}'.
            alt (string): Data format for response. Example: '{{alt}}'.
            callback (string): JSONP Example: '{{callback}}'.
            fields (string): Selector specifying which fields to include in a partial response. Example: '{{fields}}'.
            key (string): API key. Your API key identifies your project and provides you with API access, quota, and reports. Required unless you provide an OAuth 2.0 token. Example: '{{key}}'.
            oauth_token (string): OAuth 2.0 token for the current user. Example: '{{oauth_token}}'.
            prettyPrint (string): Returns response with indentations and line breaks. Example: '{{prettyPrint}}'.
            quotaUser (string): Available to use for quota purposes for server-side applications. Can be any arbitrary string assigned to a user, but should not exceed 40 characters. Example: '{{quotaUser}}'.
            upload_protocol (string): Upload protocol for media (e.g. "raw", "multipart"). Example: '{{upload_protocol}}'.
            uploadType (string): Legacy upload protocol for media (e.g. "media", "multipart"). Example: '{{uploadType}}'.
            xgafv (string): V1 error format. Example: '{{$.xgafv}}'.

        Returns:
            dict[str, Any]: Successful response

        Tags:
            Messages, important
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if id is None:
            raise ValueError("Missing required parameter 'id'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/messages/{id}/trash"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data={}, params=query_params)
        response.raise_for_status()
        return response.json()

    def untrash_messages(self, userId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Moves a message out of the trash, effectively undoing a trash action and restoring the message to the user's mailbox.

        Args:
            userId (string): userId
            id (string): id
            access_token (string): OAuth access token. Example: '{{access_token}}'.
            alt (string): Data format for response. Example: '{{alt}}'.
            callback (string): JSONP Example: '{{callback}}'.
            fields (string): Selector specifying which fields to include in a partial response. Example: '{{fields}}'.
            key (string): API key. Your API key identifies your project and provides you with API access, quota, and reports. Required unless you provide an OAuth 2.0 token. Example: '{{key}}'.
            oauth_token (string): OAuth 2.0 token for the current user. Example: '{{oauth_token}}'.
            prettyPrint (string): Returns response with indentations and line breaks. Example: '{{prettyPrint}}'.
            quotaUser (string): Available to use for quota purposes for server-side applications. Can be any arbitrary string assigned to a user, but should not exceed 40 characters. Example: '{{quotaUser}}'.
            upload_protocol (string): Upload protocol for media (e.g. "raw", "multipart"). Example: '{{upload_protocol}}'.
            uploadType (string): Legacy upload protocol for media (e.g. "media", "multipart"). Example: '{{uploadType}}'.
            xgafv (string): V1 error format. Example: '{{$.xgafv}}'.

        Returns:
            dict[str, Any]: Successful response

        Tags:
            Messages
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if id is None:
            raise ValueError("Missing required parameter 'id'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/messages/{id}/untrash"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data={}, params=query_params)
        response.raise_for_status()
        return response.json()

 
 
  

    def get_attachments(self, userId, messageId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Retrieves the actual file content of a specific attachment from a Gmail message

        Args:
            userId (string): userId
            messageId (string): messageId
            id (string): id
            access_token (string): OAuth access token. Example: '{{access_token}}'.
            alt (string): Data format for response. Example: '{{alt}}'.
            callback (string): JSONP Example: '{{callback}}'.
            fields (string): Selector specifying which fields to include in a partial response. Example: '{{fields}}'.
            key (string): API key. Your API key identifies your project and provides you with API access, quota, and reports. Required unless you provide an OAuth 2.0 token. Example: '{{key}}'.
            oauth_token (string): OAuth 2.0 token for the current user. Example: '{{oauth_token}}'.
            prettyPrint (string): Returns response with indentations and line breaks. Example: '{{prettyPrint}}'.
            quotaUser (string): Available to use for quota purposes for server-side applications. Can be any arbitrary string assigned to a user, but should not exceed 40 characters. Example: '{{quotaUser}}'.
            upload_protocol (string): Upload protocol for media (e.g. "raw", "multipart"). Example: '{{upload_protocol}}'.
            uploadType (string): Legacy upload protocol for media (e.g. "media", "multipart"). Example: '{{uploadType}}'.
            xgafv (string): V1 error format. Example: '{{$.xgafv}}'.

        Returns:
            dict[str, Any]: Successful response

        Tags:
            Messages
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if messageId is None:
            raise ValueError("Missing required parameter 'messageId'")
        if id is None:
            raise ValueError("Missing required parameter 'id'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/messages/{messageId}/attachments/{id}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()


    def update_labels(self, userId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, color=None, labelListVisibility=None, messageListVisibility=None, messagesTotal=None, messagesUnread=None, name=None, threadsTotal=None, threadsUnread=None, type=None) -> dict[str, Any]:
        """
        Update an existing Gmail label's properties such as name, color, or visibility.

        Args:
            userId (string): userId
            id (string): id
            access_token (string): OAuth access token. Example: '{{access_token}}'.
            alt (string): Data format for response. Example: '{{alt}}'.
            callback (string): JSONP Example: '{{callback}}'.
            fields (string): Selector specifying which fields to include in a partial response. Example: '{{fields}}'.
            key (string): API key. Your API key identifies your project and provides you with API access, quota, and reports. Required unless you provide an OAuth 2.0 token. Example: '{{key}}'.
            oauth_token (string): OAuth 2.0 token for the current user. Example: '{{oauth_token}}'.
            prettyPrint (string): Returns response with indentations and line breaks. Example: '{{prettyPrint}}'.
            quotaUser (string): Available to use for quota purposes for server-side applications. Can be any arbitrary string assigned to a user, but should not exceed 40 characters. Example: '{{quotaUser}}'.
            upload_protocol (string): Upload protocol for media (e.g. "raw", "multipart"). Example: '{{upload_protocol}}'.
            uploadType (string): Legacy upload protocol for media (e.g. "media", "multipart"). Example: '{{uploadType}}'.
            xgafv (string): V1 error format. Example: '{{$.xgafv}}'.
            color (object): color
            labelListVisibility (string): labelListVisibility Example: 'labelShow'.
            messageListVisibility (string): messageListVisibility Example: 'show'.
            messagesTotal (number): messagesTotal Example: '-34033607'.
            messagesUnread (number): messagesUnread Example: '96181517'.
            name (string): name Example: 'esse nulla occaecat'.
            threadsTotal (number): threadsTotal Example: '7293200'.
            threadsUnread (number): threadsUnread Example: '86726755'.
            type (string): type
                Example:
                ```json
                {
                  "color": {
                    "backgroundColor": "commodo est cupidatat in sed",
                    "textColor": "sunt fugiat ut voluptate"
                  },
                  "id": "nostrud officia pariatur",
                  "labelListVisibility": "labelShow",
                  "messageListVisibility": "show",
                  "messagesTotal": -34033607,
                  "messagesUnread": 96181517,
                  "name": "esse nulla occaecat",
                  "threadsTotal": 7293200,
                  "threadsUnread": 86726755,
                  "type": "system"
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            Labels
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if id is None:
            raise ValueError("Missing required parameter 'id'")
        request_body = {
            'color': color,
            'id': id,
            'labelListVisibility': labelListVisibility,
            'messageListVisibility': messageListVisibility,
            'messagesTotal': messagesTotal,
            'messagesUnread': messagesUnread,
            'name': name,
            'threadsTotal': threadsTotal,
            'threadsUnread': threadsUnread,
            'type': type,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/labels/{id}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._put(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def delete_labels(self, userId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> Any:
        """
        Delete a Gmail label by its ID.

        Args:
            userId (string): userId
            id (string): id
            access_token (string): OAuth access token. Example: '{{access_token}}'.
            alt (string): Data format for response. Example: '{{alt}}'.
            callback (string): JSONP Example: '{{callback}}'.
            fields (string): Selector specifying which fields to include in a partial response. Example: '{{fields}}'.
            key (string): API key. Your API key identifies your project and provides you with API access, quota, and reports. Required unless you provide an OAuth 2.0 token. Example: '{{key}}'.
            oauth_token (string): OAuth 2.0 token for the current user. Example: '{{oauth_token}}'.
            prettyPrint (string): Returns response with indentations and line breaks. Example: '{{prettyPrint}}'.
            quotaUser (string): Available to use for quota purposes for server-side applications. Can be any arbitrary string assigned to a user, but should not exceed 40 characters. Example: '{{quotaUser}}'.
            upload_protocol (string): Upload protocol for media (e.g. "raw", "multipart"). Example: '{{upload_protocol}}'.
            uploadType (string): Legacy upload protocol for media (e.g. "media", "multipart"). Example: '{{uploadType}}'.
            xgafv (string): V1 error format. Example: '{{$.xgafv}}'.

        Returns:
            Any: No Content

        Tags:
            Labels
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if id is None:
            raise ValueError("Missing required parameter 'id'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/labels/{id}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._delete(url, params=query_params)
        response.raise_for_status()
        return response.json()

 
 

    def get_filters(self, userId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Fetch Gmail filter configuration and rules by filter ID

        Args:
            userId (string): userId
            id (string): id
            access_token (string): OAuth access token. Example: '{{access_token}}'.
            alt (string): Data format for response. Example: '{{alt}}'.
            callback (string): JSONP Example: '{{callback}}'.
            fields (string): Selector specifying which fields to include in a partial response. Example: '{{fields}}'.
            key (string): API key. Your API key identifies your project and provides you with API access, quota, and reports. Required unless you provide an OAuth 2.0 token. Example: '{{key}}'.
            oauth_token (string): OAuth 2.0 token for the current user. Example: '{{oauth_token}}'.
            prettyPrint (string): Returns response with indentations and line breaks. Example: '{{prettyPrint}}'.
            quotaUser (string): Available to use for quota purposes for server-side applications. Can be any arbitrary string assigned to a user, but should not exceed 40 characters. Example: '{{quotaUser}}'.
            upload_protocol (string): Upload protocol for media (e.g. "raw", "multipart"). Example: '{{upload_protocol}}'.
            uploadType (string): Legacy upload protocol for media (e.g. "media", "multipart"). Example: '{{uploadType}}'.
            xgafv (string): V1 error format. Example: '{{$.xgafv}}'.

        Returns:
            dict[str, Any]: Successful response

        Tags:
            settings, Filters
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if id is None:
            raise ValueError("Missing required parameter 'id'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/filters/{id}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def delete_filters(self, userId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> Any:
        """
        Remove Gmail filter and its associated automation rules

        Args:
            userId (string): userId
            id (string): id
            access_token (string): OAuth access token. Example: '{{access_token}}'.
            alt (string): Data format for response. Example: '{{alt}}'.
            callback (string): JSONP Example: '{{callback}}'.
            fields (string): Selector specifying which fields to include in a partial response. Example: '{{fields}}'.
            key (string): API key. Your API key identifies your project and provides you with API access, quota, and reports. Required unless you provide an OAuth 2.0 token. Example: '{{key}}'.
            oauth_token (string): OAuth 2.0 token for the current user. Example: '{{oauth_token}}'.
            prettyPrint (string): Returns response with indentations and line breaks. Example: '{{prettyPrint}}'.
            quotaUser (string): Available to use for quota purposes for server-side applications. Can be any arbitrary string assigned to a user, but should not exceed 40 characters. Example: '{{quotaUser}}'.
            upload_protocol (string): Upload protocol for media (e.g. "raw", "multipart"). Example: '{{upload_protocol}}'.
            uploadType (string): Legacy upload protocol for media (e.g. "media", "multipart"). Example: '{{uploadType}}'.
            xgafv (string): V1 error format. Example: '{{$.xgafv}}'.

        Returns:
            Any: No Content

        Tags:
            settings, Filters
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if id is None:
            raise ValueError("Missing required parameter 'id'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/filters/{id}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._delete(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def list_filters(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Retrieve all Gmail filters and their automation settings

        Args:
            userId (string): userId
            access_token (string): OAuth access token. Example: '{{access_token}}'.
            alt (string): Data format for response. Example: '{{alt}}'.
            callback (string): JSONP Example: '{{callback}}'.
            fields (string): Selector specifying which fields to include in a partial response. Example: '{{fields}}'.
            key (string): API key. Your API key identifies your project and provides you with API access, quota, and reports. Required unless you provide an OAuth 2.0 token. Example: '{{key}}'.
            oauth_token (string): OAuth 2.0 token for the current user. Example: '{{oauth_token}}'.
            prettyPrint (string): Returns response with indentations and line breaks. Example: '{{prettyPrint}}'.
            quotaUser (string): Available to use for quota purposes for server-side applications. Can be any arbitrary string assigned to a user, but should not exceed 40 characters. Example: '{{quotaUser}}'.
            upload_protocol (string): Upload protocol for media (e.g. "raw", "multipart"). Example: '{{upload_protocol}}'.
            uploadType (string): Legacy upload protocol for media (e.g. "media", "multipart"). Example: '{{uploadType}}'.
            xgafv (string): V1 error format. Example: '{{$.xgafv}}'.

        Returns:
            dict[str, Any]: Successful response

        Tags:
            settings, Filters
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/filters"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def create_filters(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, action=None, criteria=None, id=None) -> dict[str, Any]:
        """
        Set up new Gmail filter with criteria and automated actions

        Args:
            userId (string): userId
            access_token (string): OAuth access token. Example: '{{access_token}}'.
            alt (string): Data format for response. Example: '{{alt}}'.
            callback (string): JSONP Example: '{{callback}}'.
            fields (string): Selector specifying which fields to include in a partial response. Example: '{{fields}}'.
            key (string): API key. Your API key identifies your project and provides you with API access, quota, and reports. Required unless you provide an OAuth 2.0 token. Example: '{{key}}'.
            oauth_token (string): OAuth 2.0 token for the current user. Example: '{{oauth_token}}'.
            prettyPrint (string): Returns response with indentations and line breaks. Example: '{{prettyPrint}}'.
            quotaUser (string): Available to use for quota purposes for server-side applications. Can be any arbitrary string assigned to a user, but should not exceed 40 characters. Example: '{{quotaUser}}'.
            upload_protocol (string): Upload protocol for media (e.g. "raw", "multipart"). Example: '{{upload_protocol}}'.
            uploadType (string): Legacy upload protocol for media (e.g. "media", "multipart"). Example: '{{uploadType}}'.
            xgafv (string): V1 error format. Example: '{{$.xgafv}}'.
            action (object): action
            criteria (object): criteria
            id (string): id
                Example:
                ```json
                {
                  "action": {
                    "addLabelIds": [
                      "nostrud laboris sed esse",
                      "et ad"
                    ],
                    "forward": "culpa do",
                    "removeLabelIds": [
                      "Lorem consequat l",
                      "minim Excepteur"
                    ]
                  },
                  "criteria": {
                    "excludeChats": false,
                    "from": "nulla adipisicing veniam et mollit",
                    "hasAttachment": true,
                    "negatedQuery": "exercitation laboris",
                    "query": "nulla cupidatat officia commodo laborum",
                    "size": -52983385,
                    "sizeComparison": "smaller",
                    "subject": "sit exercitation",
                    "to": "veniam commodo"
                  },
                  "id": "in aute anim"
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            settings, Filters
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        request_body = {
            'action': action,
            'criteria': criteria,
            'id': id,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/filters"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def list_tools(self):
        return [
            self.send_email,
            self.create_draft,
            self.send_draft,
            self.get_draft,
            self.list_drafts,
            self.get_message,
            self.list_messages,
            self.list_labels,
            self.create_label,
            self.get_profile,
            # Auto Generated from openapi spec
         
            self.update_drafts,
         
            self.trash_messsages,
            self.untrash_messages,
         
         
            self.get_attachments,

            self.update_labels,
            self.delete_labels,
           
            self.get_filters,
            self.delete_filters,
            self.list_filters,
            self.create_filters,
      
        ]
