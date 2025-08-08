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


    def watch_users(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, labelFilterAction=None, labelFilterBehavior=None, labelIds=None, topicName=None) -> dict[str, Any]:
        """
        Watch Users

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
            labelFilterAction (string): labelFilterAction Example: 'exclude'.
            labelFilterBehavior (string): labelFilterBehavior Example: 'include'.
            labelIds (array): labelIds Example: "['officia ex reprehenderit et', 'labore ullamco ut']".
            topicName (string): topicName
                Example:
                ```json
                {
                  "labelFilterAction": "exclude",
                  "labelFilterBehavior": "include",
                  "labelIds": [
                    "officia ex reprehenderit et",
                    "labore ullamco ut"
                  ],
                  "topicName": "Ut enim in in"
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            Notifications
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        request_body = {
            'labelFilterAction': labelFilterAction,
            'labelFilterBehavior': labelFilterBehavior,
            'labelIds': labelIds,
            'topicName': topicName,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/watch"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def stop_notifications_for_user(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> Any:
        """
        Stop Notifications for User

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
            Any: No Content

        Tags:
            Notifications
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/stop"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data={}, params=query_params)
        response.raise_for_status()
        return response.json()

    def send_drafts(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, id=None, message=None) -> dict[str, Any]:
        """
        Send Drafts

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
            id (string): id Example: 'elit Lorem'.
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
        request_body = {
            'id': id,
            'message': message,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/drafts/send"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_drafts(self, userId, id, format=None, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Get Drafts

        Args:
            userId (string): userId
            id (string): id
            format (string): No description provided. Example: '{{format}}'.
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
            Drafts
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if id is None:
            raise ValueError("Missing required parameter 'id'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/drafts/{id}"
        query_params = {k: v for k, v in [('format', format), ('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def update_drafts(self, userId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, message=None) -> dict[str, Any]:
        """
        Update Drafts

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

    def delete_drafts(self, userId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> Any:
        """
        Delete Drafts

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
            Drafts
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if id is None:
            raise ValueError("Missing required parameter 'id'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/drafts/{id}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._delete(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def create_drafts(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, id=None, message=None) -> dict[str, Any]:
        """
        Create Drafts

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
            id (string): id Example: 'elit Lorem'.
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
        request_body = {
            'id': id,
            'message': message,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/drafts"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def list_history(self, userId, maxResults=None, pageToken=None, startHistoryId=None, labelId=None, historyTypes=None, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        List History

        Args:
            userId (string): userId
            maxResults (string): No description provided. Example: '{{maxResults}}'.
            pageToken (string): No description provided. Example: '{{pageToken}}'.
            startHistoryId (string): No description provided. Example: '{{startHistoryId}}'.
            labelId (string): No description provided. Example: '{{labelId}}'.
            historyTypes (string): No description provided. Example: '{{historyTypes}}'.
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
            History
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/history"
        query_params = {k: v for k, v in [('maxResults', maxResults), ('pageToken', pageToken), ('startHistoryId', startHistoryId), ('labelId', labelId), ('historyTypes', historyTypes), ('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def trash_messsages(self, userId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Trash Messsages

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
        url = f"{self.base_url}/gmail/v1/users/{userId}/messages/{id}/trash"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data={}, params=query_params)
        response.raise_for_status()
        return response.json()

    def untrash_messages(self, userId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Untrash Messages

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

    def modify_messages(self, userId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, addLabelIds=None, removeLabelIds=None) -> dict[str, Any]:
        """
        Modify Messages

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
            addLabelIds (array): addLabelIds Example: "['qui eu do ex', 'do sit esse dolor proident']".
            removeLabelIds (array): removeLabelIds
                Example:
                ```json
                {
                  "addLabelIds": [
                    "qui eu do ex",
                    "do sit esse dolor proident"
                  ],
                  "removeLabelIds": [
                    "Lorem sit",
                    "sed"
                  ]
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            Messages
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if id is None:
            raise ValueError("Missing required parameter 'id'")
        request_body = {
            'addLabelIds': addLabelIds,
            'removeLabelIds': removeLabelIds,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/messages/{id}/modify"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def batch_delete(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, ids=None) -> Any:
        """
        Batch Delete

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
            ids (array): ids
                Example:
                ```json
                {
                  "ids": [
                    "labore conseq",
                    "sit"
                  ]
                }
                ```

        Returns:
            Any: No Content

        Tags:
            Messages
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        request_body = {
            'ids': ids,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/messages/batchDelete"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def import_messages(self, userId, internalDateSource=None, neverMarkSpam=None, processForCalendar=None, deleted=None, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, historyId=None, id=None, internalDate=None, labelIds=None, payload=None, raw=None, sizeEstimate=None, snippet=None, threadId=None) -> dict[str, Any]:
        """
        Import Messages

        Args:
            userId (string): userId
            internalDateSource (string): No description provided. Example: '{{internalDateSource}}'.
            neverMarkSpam (string): No description provided. Example: '{{neverMarkSpam}}'.
            processForCalendar (string): No description provided. Example: '{{processForCalendar}}'.
            deleted (string): No description provided. Example: '{{deleted}}'.
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
            historyId (string): historyId Example: 'nisi tempor do'.
            id (string): id Example: 'eu incididunt laborum irure'.
            internalDate (string): internalDate Example: 'cupidatat officia anim'.
            labelIds (array): labelIds Example: "['mollit amet dolore cupidatat', 'cupidatat deserunt mollit']".
            payload (object): payload
            raw (string): raw Example: 'do laboris'.
            sizeEstimate (number): sizeEstimate Example: '21128811'.
            snippet (string): snippet Example: 'ut dolor'.
            threadId (string): threadId
                Example:
                ```json
                {
                  "historyId": "nisi tempor do",
                  "id": "eu incididunt laborum irure",
                  "internalDate": "cupidatat officia anim",
                  "labelIds": [
                    "mollit amet dolore cupidatat",
                    "cupidatat deserunt mollit"
                  ],
                  "payload": {
                    "body": {
                      "attachmentId": "id nulla consequat",
                      "data": "ad in occaecat",
                      "size": -93837667
                    },
                    "filename": "ea commodo dolor nisi",
                    "headers": [
                      {
                        "name": "quis id velit laborum",
                        "value": "et voluptate dolor ea"
                      },
                      {
                        "name": "sit nostrud",
                        "value": "deserunt fugiat ex"
                      }
                    ],
                    "mimeType": "sit dolor mollit",
                    "partId": "dolore velit incididunt est a",
                    "parts": [
                      {
                        "value": "<Circular reference to #/components/schemas/MessagePart detected>"
                      },
                      {
                        "value": "<Circular reference to #/components/schemas/MessagePart detected>"
                      }
                    ]
                  },
                  "raw": "do laboris",
                  "sizeEstimate": 21128811,
                  "snippet": "ut dolor",
                  "threadId": "magna Ut officia"
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            Messages
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        request_body = {
            'historyId': historyId,
            'id': id,
            'internalDate': internalDate,
            'labelIds': labelIds,
            'payload': payload,
            'raw': raw,
            'sizeEstimate': sizeEstimate,
            'snippet': snippet,
            'threadId': threadId,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/messages/import"
        query_params = {k: v for k, v in [('internalDateSource', internalDateSource), ('neverMarkSpam', neverMarkSpam), ('processForCalendar', processForCalendar), ('deleted', deleted), ('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def send_messages(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, historyId=None, id=None, internalDate=None, labelIds=None, payload=None, raw=None, sizeEstimate=None, snippet=None, threadId=None) -> dict[str, Any]:
        """
        Send Messages

        Args:
            userId (string): userId
            access_token (string): OAuth access token. Example: '{{accessToken}}'.
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
            historyId (string): historyId Example: 'nisi tempor do'.
            id (string): id Example: 'eu incididunt laborum irure'.
            internalDate (string): internalDate Example: 'cupidatat officia anim'.
            labelIds (array): labelIds Example: "['mollit amet dolore cupidatat', 'cupidatat deserunt mollit']".
            payload (object): payload
            raw (string): raw Example: 'do laboris'.
            sizeEstimate (number): sizeEstimate Example: '21128811'.
            snippet (string): snippet Example: 'ut dolor'.
            threadId (string): threadId
                Example:
                ```json
                {
                  "historyId": "nisi tempor do",
                  "id": "eu incididunt laborum irure",
                  "internalDate": "cupidatat officia anim",
                  "labelIds": [
                    "mollit amet dolore cupidatat",
                    "cupidatat deserunt mollit"
                  ],
                  "payload": {
                    "body": {
                      "attachmentId": "id nulla consequat",
                      "data": "ad in occaecat",
                      "size": -93837667
                    },
                    "filename": "ea commodo dolor nisi",
                    "headers": [
                      {
                        "name": "quis id velit laborum",
                        "value": "et voluptate dolor ea"
                      },
                      {
                        "name": "sit nostrud",
                        "value": "deserunt fugiat ex"
                      }
                    ],
                    "mimeType": "sit dolor mollit",
                    "partId": "dolore velit incididunt est a",
                    "parts": [
                      {
                        "value": "<Circular reference to #/components/schemas/MessagePart detected>"
                      },
                      {
                        "value": "<Circular reference to #/components/schemas/MessagePart detected>"
                      }
                    ]
                  },
                  "raw": "do laboris",
                  "sizeEstimate": 21128811,
                  "snippet": "ut dolor",
                  "threadId": "magna Ut officia"
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            Messages
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        request_body = {
            'historyId': historyId,
            'id': id,
            'internalDate': internalDate,
            'labelIds': labelIds,
            'payload': payload,
            'raw': raw,
            'sizeEstimate': sizeEstimate,
            'snippet': snippet,
            'threadId': threadId,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/messages/send"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def batch_modify(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, addLabelIds=None, ids=None, removeLabelIds=None) -> Any:
        """
        Batch Modify

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
            addLabelIds (array): addLabelIds Example: "['irure Lorem ex proident', 'proident ']".
            ids (array): ids Example: "['ullamco aliqua anim dolo', 'irure ea']".
            removeLabelIds (array): removeLabelIds
                Example:
                ```json
                {
                  "addLabelIds": [
                    "irure Lorem ex proident",
                    "proident "
                  ],
                  "ids": [
                    "ullamco aliqua anim dolo",
                    "irure ea"
                  ],
                  "removeLabelIds": [
                    "do anim ad nulla",
                    "minim irure"
                  ]
                }
                ```

        Returns:
            Any: No Content

        Tags:
            Messages
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        request_body = {
            'addLabelIds': addLabelIds,
            'ids': ids,
            'removeLabelIds': removeLabelIds,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/messages/batchModify"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def insert_messages(self, userId, internalDateSource=None, deleted=None, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, historyId=None, id=None, internalDate=None, labelIds=None, payload=None, raw=None, sizeEstimate=None, snippet=None, threadId=None) -> dict[str, Any]:
        """
        Insert Messages

        Args:
            userId (string): userId
            internalDateSource (string): No description provided. Example: '{{internalDateSource}}'.
            deleted (string): No description provided. Example: '{{deleted}}'.
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
            historyId (string): historyId Example: 'nisi tempor do'.
            id (string): id Example: 'eu incididunt laborum irure'.
            internalDate (string): internalDate Example: 'cupidatat officia anim'.
            labelIds (array): labelIds Example: "['mollit amet dolore cupidatat', 'cupidatat deserunt mollit']".
            payload (object): payload
            raw (string): raw Example: 'do laboris'.
            sizeEstimate (number): sizeEstimate Example: '21128811'.
            snippet (string): snippet Example: 'ut dolor'.
            threadId (string): threadId
                Example:
                ```json
                {
                  "historyId": "nisi tempor do",
                  "id": "eu incididunt laborum irure",
                  "internalDate": "cupidatat officia anim",
                  "labelIds": [
                    "mollit amet dolore cupidatat",
                    "cupidatat deserunt mollit"
                  ],
                  "payload": {
                    "body": {
                      "attachmentId": "id nulla consequat",
                      "data": "ad in occaecat",
                      "size": -93837667
                    },
                    "filename": "ea commodo dolor nisi",
                    "headers": [
                      {
                        "name": "quis id velit laborum",
                        "value": "et voluptate dolor ea"
                      },
                      {
                        "name": "sit nostrud",
                        "value": "deserunt fugiat ex"
                      }
                    ],
                    "mimeType": "sit dolor mollit",
                    "partId": "dolore velit incididunt est a",
                    "parts": [
                      {
                        "value": "<Circular reference to #/components/schemas/MessagePart detected>"
                      },
                      {
                        "value": "<Circular reference to #/components/schemas/MessagePart detected>"
                      }
                    ]
                  },
                  "raw": "do laboris",
                  "sizeEstimate": 21128811,
                  "snippet": "ut dolor",
                  "threadId": "magna Ut officia"
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            Messages
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        request_body = {
            'historyId': historyId,
            'id': id,
            'internalDate': internalDate,
            'labelIds': labelIds,
            'payload': payload,
            'raw': raw,
            'sizeEstimate': sizeEstimate,
            'snippet': snippet,
            'threadId': threadId,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/messages"
        query_params = {k: v for k, v in [('internalDateSource', internalDateSource), ('deleted', deleted), ('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_messages(self, userId, id, format=None, metadataHeaders=None, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Get Messages

        Args:
            userId (string): userId
            id (string): id
            format (string): No description provided. Example: '{{format}}'.
            metadataHeaders (string): No description provided. Example: '{{metadataHeaders}}'.
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
        url = f"{self.base_url}/gmail/v1/users/{userId}/messages/{id}"
        query_params = {k: v for k, v in [('format', format), ('metadataHeaders', metadataHeaders), ('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def delete_messages(self, userId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> Any:
        """
        Delete Messages

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
            Messages
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if id is None:
            raise ValueError("Missing required parameter 'id'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/messages/{id}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._delete(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_attachments(self, userId, messageId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Get Attachments

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

    def create_labels(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, color=None, id=None, labelListVisibility=None, messageListVisibility=None, messagesTotal=None, messagesUnread=None, name=None, threadsTotal=None, threadsUnread=None, type=None) -> dict[str, Any]:
        """
        Create Labels

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
            color (object): color
            id (string): id Example: 'nostrud officia pariatur'.
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
        url = f"{self.base_url}/gmail/v1/users/{userId}/labels"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_labels(self, userId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Get Labels

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
            Labels
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if id is None:
            raise ValueError("Missing required parameter 'id'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/labels/{id}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def update_labels(self, userId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, color=None, labelListVisibility=None, messageListVisibility=None, messagesTotal=None, messagesUnread=None, name=None, threadsTotal=None, threadsUnread=None, type=None) -> dict[str, Any]:
        """
        Update Labels

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
        Delete Labels

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

    def patch_labels(self, userId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, color=None, labelListVisibility=None, messageListVisibility=None, messagesTotal=None, messagesUnread=None, name=None, threadsTotal=None, threadsUnread=None, type=None) -> dict[str, Any]:
        """
        Patch Labels

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
        response = self._patch(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_threads(self, userId, id, format=None, metadataHeaders=None, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Get Threads

        Args:
            userId (string): userId
            id (string): id
            format (string): No description provided. Example: '{{format}}'.
            metadataHeaders (string): No description provided. Example: '{{metadataHeaders}}'.
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
            Theads
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if id is None:
            raise ValueError("Missing required parameter 'id'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/threads/{id}"
        query_params = {k: v for k, v in [('format', format), ('metadataHeaders', metadataHeaders), ('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def delete_threads(self, userId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> Any:
        """
        Delete Threads

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
            Theads
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if id is None:
            raise ValueError("Missing required parameter 'id'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/threads/{id}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._delete(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def modify_threads(self, userId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, addLabelIds=None, removeLabelIds=None) -> dict[str, Any]:
        """
        Modify Threads

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
            addLabelIds (array): addLabelIds Example: "['labore anim culpa aliqua', 'Duis sed irure Ut aliqua']".
            removeLabelIds (array): removeLabelIds
                Example:
                ```json
                {
                  "addLabelIds": [
                    "labore anim culpa aliqua",
                    "Duis sed irure Ut aliqua"
                  ],
                  "removeLabelIds": [
                    "consectetur et dolore Lorem",
                    "reprehenderit tempor id dolore incididunt"
                  ]
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            Theads
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if id is None:
            raise ValueError("Missing required parameter 'id'")
        request_body = {
            'addLabelIds': addLabelIds,
            'removeLabelIds': removeLabelIds,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/threads/{id}/modify"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def trash_threads(self, userId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Trash Threads

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
            Theads
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if id is None:
            raise ValueError("Missing required parameter 'id'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/threads/{id}/trash"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data={}, params=query_params)
        response.raise_for_status()
        return response.json()

    def list_threads(self, userId, maxResults=None, pageToken=None, q=None, labelIds=None, includeSpamTrash=None, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        List Threads

        Args:
            userId (string): userId
            maxResults (string): No description provided. Example: '{{maxResults}}'.
            pageToken (string): No description provided. Example: '{{pageToken}}'.
            q (string): No description provided. Example: '{{q}}'.
            labelIds (string): No description provided. Example: '{{labelIds}}'.
            includeSpamTrash (string): No description provided. Example: '{{includeSpamTrash}}'.
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
            Theads
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/threads"
        query_params = {k: v for k, v in [('maxResults', maxResults), ('pageToken', pageToken), ('q', q), ('labelIds', labelIds), ('includeSpamTrash', includeSpamTrash), ('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_imap(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        GET IMAP

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
            settings, imap
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/imap"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def update_imap(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, autoExpunge=None, enabled=None, expungeBehavior=None, maxFolderSize=None) -> dict[str, Any]:
        """
        Update IMAP

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
            autoExpunge (boolean): autoExpunge Example: 'False'.
            enabled (boolean): enabled Example: 'False'.
            expungeBehavior (string): expungeBehavior Example: 'deleteForever'.
            maxFolderSize (number): maxFolderSize
                Example:
                ```json
                {
                  "autoExpunge": false,
                  "enabled": false,
                  "expungeBehavior": "deleteForever",
                  "maxFolderSize": -49364914
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            settings, imap
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        request_body = {
            'autoExpunge': autoExpunge,
            'enabled': enabled,
            'expungeBehavior': expungeBehavior,
            'maxFolderSize': maxFolderSize,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/imap"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._put(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_pop_settings(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Get POP Settings

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
            settings, pop
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/pop"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def update_pop_settings(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, accessWindow=None, disposition=None) -> dict[str, Any]:
        """
        Update POP Settings

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
            accessWindow (string): accessWindow Example: 'fromNowOn'.
            disposition (string): disposition
                Example:
                ```json
                {
                  "accessWindow": "fromNowOn",
                  "disposition": "dispositionUnspecified"
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            settings, pop
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        request_body = {
            'accessWindow': accessWindow,
            'disposition': disposition,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/pop"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._put(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_vacation_settings(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Get Vacation Settings

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
            settings, vacation
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/vacation"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def update_vacation_settings(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, enableAutoReply=None, endTime=None, responseBodyHtml=None, responseBodyPlainText=None, responseSubject=None, restrictToContacts=None, restrictToDomain=None, startTime=None) -> dict[str, Any]:
        """
        Update Vacation Settings

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
            enableAutoReply (boolean): enableAutoReply Example: 'False'.
            endTime (string): endTime Example: 'enim in aliqua Ut commodo'.
            responseBodyHtml (string): responseBodyHtml Example: 'id'.
            responseBodyPlainText (string): responseBodyPlainText Example: 'veniam reprehe'.
            responseSubject (string): responseSubject Example: 'ei'.
            restrictToContacts (boolean): restrictToContacts Example: 'False'.
            restrictToDomain (boolean): restrictToDomain Example: 'True'.
            startTime (string): startTime
                Example:
                ```json
                {
                  "enableAutoReply": false,
                  "endTime": "enim in aliqua Ut commodo",
                  "responseBodyHtml": "id",
                  "responseBodyPlainText": "veniam reprehe",
                  "responseSubject": "ei",
                  "restrictToContacts": false,
                  "restrictToDomain": true,
                  "startTime": "est mollit"
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            settings, vacation
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        request_body = {
            'enableAutoReply': enableAutoReply,
            'endTime': endTime,
            'responseBodyHtml': responseBodyHtml,
            'responseBodyPlainText': responseBodyPlainText,
            'responseSubject': responseSubject,
            'restrictToContacts': restrictToContacts,
            'restrictToDomain': restrictToDomain,
            'startTime': startTime,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/vacation"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._put(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_language_settings(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Get Language Settings

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
            settings, language
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/language"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def update_language_settings(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, displayLanguage=None) -> dict[str, Any]:
        """
        Update Language Settings

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
            displayLanguage (string): displayLanguage
                Example:
                ```json
                {
                  "displayLanguage": "occaecat adipisicing"
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            settings, language
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        request_body = {
            'displayLanguage': displayLanguage,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/language"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._put(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_auto_forwarding_settings(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Get Auto Forwarding Settings

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
            settings, autoForwarding
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/autoForwarding"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def update_auto_forwarding(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, disposition=None, emailAddress=None, enabled=None) -> dict[str, Any]:
        """
        Update Auto Forwarding

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
            disposition (string): disposition Example: 'trash'.
            emailAddress (string): emailAddress Example: 'officia ullamco Ut laboris eu'.
            enabled (boolean): enabled
                Example:
                ```json
                {
                  "disposition": "trash",
                  "emailAddress": "officia ullamco Ut laboris eu",
                  "enabled": false
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            settings, autoForwarding
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        request_body = {
            'disposition': disposition,
            'emailAddress': emailAddress,
            'enabled': enabled,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/autoForwarding"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._put(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def set_default_smime_config(self, userId, sendAsEmail, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> Any:
        """
        Set default S/MIME config

        Args:
            userId (string): userId
            sendAsEmail (string): sendAsEmail
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
            settings, Send As, Send As Email, SMIME INFO, Set Default
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if sendAsEmail is None:
            raise ValueError("Missing required parameter 'sendAsEmail'")
        if id is None:
            raise ValueError("Missing required parameter 'id'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/sendAs/{sendAsEmail}/smimeInfo/{id}/setDefault"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data={}, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_send_as_smime_info(self, userId, sendAsEmail, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Get Send As SMIME Info

        Args:
            userId (string): userId
            sendAsEmail (string): sendAsEmail
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
            settings, Send As, Send As Email, SMIME INFO
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if sendAsEmail is None:
            raise ValueError("Missing required parameter 'sendAsEmail'")
        if id is None:
            raise ValueError("Missing required parameter 'id'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/sendAs/{sendAsEmail}/smimeInfo/{id}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def delete_send_as_smime_info(self, userId, sendAsEmail, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> Any:
        """
        Delete Send As SMIME INfo

        Args:
            userId (string): userId
            sendAsEmail (string): sendAsEmail
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
            settings, Send As, Send As Email, SMIME INFO
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if sendAsEmail is None:
            raise ValueError("Missing required parameter 'sendAsEmail'")
        if id is None:
            raise ValueError("Missing required parameter 'id'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/sendAs/{sendAsEmail}/smimeInfo/{id}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._delete(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def list_smime_info(self, userId, sendAsEmail, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        List SMIME Info

        Args:
            userId (string): userId
            sendAsEmail (string): sendAsEmail
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
            settings, Send As, Send As Email, SMIME INFO
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if sendAsEmail is None:
            raise ValueError("Missing required parameter 'sendAsEmail'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/sendAs/{sendAsEmail}/smimeInfo"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def insert_smime_info(self, userId, sendAsEmail, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, encryptedKeyPassword=None, expiration=None, id=None, isDefault=None, issuerCn=None, pem=None, pkcs12=None) -> dict[str, Any]:
        """
        Insert SMIME Info

        Args:
            userId (string): userId
            sendAsEmail (string): sendAsEmail
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
            encryptedKeyPassword (string): encryptedKeyPassword Example: 'cillum ut'.
            expiration (string): expiration Example: 'dolore magna'.
            id (string): id Example: 'id'.
            isDefault (boolean): isDefault Example: 'False'.
            issuerCn (string): issuerCn Example: 'ipsum qui s'.
            pem (string): pem Example: 'cillum labore '.
            pkcs12 (string): pkcs12
                Example:
                ```json
                {
                  "encryptedKeyPassword": "cillum ut",
                  "expiration": "dolore magna",
                  "id": "id",
                  "isDefault": false,
                  "issuerCn": "ipsum qui s",
                  "pem": "cillum labore ",
                  "pkcs12": "in aute et"
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            settings, Send As, Send As Email, SMIME INFO
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if sendAsEmail is None:
            raise ValueError("Missing required parameter 'sendAsEmail'")
        request_body = {
            'encryptedKeyPassword': encryptedKeyPassword,
            'expiration': expiration,
            'id': id,
            'isDefault': isDefault,
            'issuerCn': issuerCn,
            'pem': pem,
            'pkcs12': pkcs12,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/sendAs/{sendAsEmail}/smimeInfo"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def verify_send_as(self, userId, sendAsEmail, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> Any:
        """
        Verify Send As

        Args:
            userId (string): userId
            sendAsEmail (string): sendAsEmail
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
            settings, Send As, Send As Email
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if sendAsEmail is None:
            raise ValueError("Missing required parameter 'sendAsEmail'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/sendAs/{sendAsEmail}/verify"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data={}, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_send_as(self, userId, sendAsEmail, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Get Send As

        Args:
            userId (string): userId
            sendAsEmail (string): sendAsEmail
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
            settings, Send As, Send As Email
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if sendAsEmail is None:
            raise ValueError("Missing required parameter 'sendAsEmail'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/sendAs/{sendAsEmail}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def update_send_as_setting(self, userId, sendAsEmail, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, displayName=None, isDefault=None, isPrimary=None, replyToAddress=None, signature=None, smtpMsa=None, treatAsAlias=None, verificationStatus=None) -> dict[str, Any]:
        """
        Update Send As Setting

        Args:
            userId (string): userId
            sendAsEmail (string): sendAsEmail
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
            displayName (string): displayName Example: 'Excepteur'.
            isDefault (boolean): isDefault Example: 'True'.
            isPrimary (boolean): isPrimary Example: 'True'.
            replyToAddress (string): replyToAddress Example: 'velit id culpa'.
            signature (string): signature Example: 'officia quis adipisicing'.
            smtpMsa (object): smtpMsa
            treatAsAlias (boolean): treatAsAlias Example: 'False'.
            verificationStatus (string): verificationStatus
                Example:
                ```json
                {
                  "displayName": "Excepteur",
                  "isDefault": true,
                  "isPrimary": true,
                  "replyToAddress": "velit id culpa",
                  "sendAsEmail": "ut nulla",
                  "signature": "officia quis adipisicing",
                  "smtpMsa": {
                    "host": "in elit",
                    "password": "tempor dolor velit",
                    "port": -34532702,
                    "securityMode": "securityModeUnspecified",
                    "username": "aliqua laborum aliquip do"
                  },
                  "treatAsAlias": false,
                  "verificationStatus": "pending"
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            settings, Send As, Send As Email
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if sendAsEmail is None:
            raise ValueError("Missing required parameter 'sendAsEmail'")
        request_body = {
            'displayName': displayName,
            'isDefault': isDefault,
            'isPrimary': isPrimary,
            'replyToAddress': replyToAddress,
            'sendAsEmail': sendAsEmail,
            'signature': signature,
            'smtpMsa': smtpMsa,
            'treatAsAlias': treatAsAlias,
            'verificationStatus': verificationStatus,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/sendAs/{sendAsEmail}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._put(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def delete_send_as(self, userId, sendAsEmail, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> Any:
        """
        Delete Send As

        Args:
            userId (string): userId
            sendAsEmail (string): sendAsEmail
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
            settings, Send As, Send As Email
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if sendAsEmail is None:
            raise ValueError("Missing required parameter 'sendAsEmail'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/sendAs/{sendAsEmail}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._delete(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def patch_send_as(self, userId, sendAsEmail, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, displayName=None, isDefault=None, isPrimary=None, replyToAddress=None, signature=None, smtpMsa=None, treatAsAlias=None, verificationStatus=None) -> dict[str, Any]:
        """
        Patch Send As

        Args:
            userId (string): userId
            sendAsEmail (string): sendAsEmail
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
            displayName (string): displayName Example: 'Excepteur'.
            isDefault (boolean): isDefault Example: 'True'.
            isPrimary (boolean): isPrimary Example: 'True'.
            replyToAddress (string): replyToAddress Example: 'velit id culpa'.
            signature (string): signature Example: 'officia quis adipisicing'.
            smtpMsa (object): smtpMsa
            treatAsAlias (boolean): treatAsAlias Example: 'False'.
            verificationStatus (string): verificationStatus
                Example:
                ```json
                {
                  "displayName": "Excepteur",
                  "isDefault": true,
                  "isPrimary": true,
                  "replyToAddress": "velit id culpa",
                  "sendAsEmail": "ut nulla",
                  "signature": "officia quis adipisicing",
                  "smtpMsa": {
                    "host": "in elit",
                    "password": "tempor dolor velit",
                    "port": -34532702,
                    "securityMode": "securityModeUnspecified",
                    "username": "aliqua laborum aliquip do"
                  },
                  "treatAsAlias": false,
                  "verificationStatus": "pending"
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            settings, Send As, Send As Email
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if sendAsEmail is None:
            raise ValueError("Missing required parameter 'sendAsEmail'")
        request_body = {
            'displayName': displayName,
            'isDefault': isDefault,
            'isPrimary': isPrimary,
            'replyToAddress': replyToAddress,
            'sendAsEmail': sendAsEmail,
            'signature': signature,
            'smtpMsa': smtpMsa,
            'treatAsAlias': treatAsAlias,
            'verificationStatus': verificationStatus,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/sendAs/{sendAsEmail}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._patch(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_send_as1(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Get Send As

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
            settings, Send As
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/sendAs"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def create_send_as(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, displayName=None, isDefault=None, isPrimary=None, replyToAddress=None, sendAsEmail=None, signature=None, smtpMsa=None, treatAsAlias=None, verificationStatus=None) -> dict[str, Any]:
        """
        Create Send As

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
            displayName (string): displayName Example: 'Excepteur'.
            isDefault (boolean): isDefault Example: 'True'.
            isPrimary (boolean): isPrimary Example: 'True'.
            replyToAddress (string): replyToAddress Example: 'velit id culpa'.
            sendAsEmail (string): sendAsEmail Example: 'ut nulla'.
            signature (string): signature Example: 'officia quis adipisicing'.
            smtpMsa (object): smtpMsa
            treatAsAlias (boolean): treatAsAlias Example: 'False'.
            verificationStatus (string): verificationStatus
                Example:
                ```json
                {
                  "displayName": "Excepteur",
                  "isDefault": true,
                  "isPrimary": true,
                  "replyToAddress": "velit id culpa",
                  "sendAsEmail": "ut nulla",
                  "signature": "officia quis adipisicing",
                  "smtpMsa": {
                    "host": "in elit",
                    "password": "tempor dolor velit",
                    "port": -34532702,
                    "securityMode": "securityModeUnspecified",
                    "username": "aliqua laborum aliquip do"
                  },
                  "treatAsAlias": false,
                  "verificationStatus": "pending"
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            settings, Send As
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        request_body = {
            'displayName': displayName,
            'isDefault': isDefault,
            'isPrimary': isPrimary,
            'replyToAddress': replyToAddress,
            'sendAsEmail': sendAsEmail,
            'signature': signature,
            'smtpMsa': smtpMsa,
            'treatAsAlias': treatAsAlias,
            'verificationStatus': verificationStatus,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/sendAs"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_cse_keypairs(self, userId, keyPairId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        GET CSE Keypairs

        Args:
            userId (string): userId
            keyPairId (string): keyPairId
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
            settings, CSE Identites, Key Pairs
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if keyPairId is None:
            raise ValueError("Missing required parameter 'keyPairId'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/cse/keypairs/{keyPairId}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def list_cse_keypairs(self, userId, pageToken=None, pageSize=None, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        List CSE Keypairs

        Args:
            userId (string): userId
            pageToken (string): No description provided. Example: '{{pageToken}}'.
            pageSize (string): No description provided. Example: '{{pageSize}}'.
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
            settings, CSE Identites, Key Pairs
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/cse/keypairs"
        query_params = {k: v for k, v in [('pageToken', pageToken), ('pageSize', pageSize), ('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def create_cse_keypairs(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, disableTime=None, enablementState=None, keyPairId=None, pem=None, pkcs7=None, privateKeyMetadata=None, subjectEmailAddresses=None) -> dict[str, Any]:
        """
        Create CSE Keypairs

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
            disableTime (string): disableTime Example: 'cill'.
            enablementState (string): enablementState Example: 'disabled'.
            keyPairId (string): keyPairId Example: 'Lorem eiusmod'.
            pem (string): pem Example: 'irure quis'.
            pkcs7 (string): pkcs7 Example: 'ex incididunt'.
            privateKeyMetadata (array): privateKeyMetadata Example: "[{'hardwareKeyMetadata': {'description': 'mollit la'}, 'kaclsKeyMetadata': {'kaclsData': 'Duis laborum aute', 'kaclsUri': 'voluptate ipsum ad'}, 'privateKeyMetadataId': 'proident fugiat eu dolore'}, {'hardwareKeyMetadata': {'description': 'ut'}, 'kaclsKeyMetadata': {'kaclsData': 'sint eiusmod', 'kaclsUri': 'minim in'}, 'privateKeyMetadataId': 'nulla ullamco'}]".
            subjectEmailAddresses (array): subjectEmailAddresses
                Example:
                ```json
                {
                  "disableTime": "cill",
                  "enablementState": "disabled",
                  "keyPairId": "Lorem eiusmod",
                  "pem": "irure quis",
                  "pkcs7": "ex incididunt",
                  "privateKeyMetadata": [
                    {
                      "hardwareKeyMetadata": {
                        "description": "mollit la"
                      },
                      "kaclsKeyMetadata": {
                        "kaclsData": "Duis laborum aute",
                        "kaclsUri": "voluptate ipsum ad"
                      },
                      "privateKeyMetadataId": "proident fugiat eu dolore"
                    },
                    {
                      "hardwareKeyMetadata": {
                        "description": "ut"
                      },
                      "kaclsKeyMetadata": {
                        "kaclsData": "sint eiusmod",
                        "kaclsUri": "minim in"
                      },
                      "privateKeyMetadataId": "nulla ullamco"
                    }
                  ],
                  "subjectEmailAddresses": [
                    "Excepteur Ut commodo aliquip",
                    "eu Lorem nulla"
                  ]
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            settings, CSE Identites, Key Pairs
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        request_body = {
            'disableTime': disableTime,
            'enablementState': enablementState,
            'keyPairId': keyPairId,
            'pem': pem,
            'pkcs7': pkcs7,
            'privateKeyMetadata': privateKeyMetadata,
            'subjectEmailAddresses': subjectEmailAddresses,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/cse/keypairs"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def list_cse_identites(self, userId, pageToken=None, pageSize=None, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        List CSE Identites

        Args:
            userId (string): userId
            pageToken (string): No description provided. Example: '{{pageToken}}'.
            pageSize (string): No description provided. Example: '{{pageSize}}'.
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
            settings, CSE Identites
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/cse/identities"
        query_params = {k: v for k, v in [('pageToken', pageToken), ('pageSize', pageSize), ('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def create_cse_identites(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, emailAddress=None, primaryKeyPairId=None, signAndEncryptKeyPairs=None) -> dict[str, Any]:
        """
        Create CSE Identites

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
            emailAddress (string): emailAddress Example: 'aliquip quis id'.
            primaryKeyPairId (string): primaryKeyPairId Example: 'in exercitation esse'.
            signAndEncryptKeyPairs (object): signAndEncryptKeyPairs
                Example:
                ```json
                {
                  "emailAddress": "aliquip quis id",
                  "primaryKeyPairId": "in exercitation esse",
                  "signAndEncryptKeyPairs": {
                    "encryptionKeyPairId": "elit nulla esse ut",
                    "signingKeyPairId": "est deserunt"
                  }
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            settings, CSE Identites
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        request_body = {
            'emailAddress': emailAddress,
            'primaryKeyPairId': primaryKeyPairId,
            'signAndEncryptKeyPairs': signAndEncryptKeyPairs,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/cse/identities"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def patch_cse_identites(self, userId, emailAddress, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, primaryKeyPairId=None, signAndEncryptKeyPairs=None) -> dict[str, Any]:
        """
        PATCH CSE Identites

        Args:
            userId (string): userId
            emailAddress (string): emailAddress
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
            primaryKeyPairId (string): primaryKeyPairId Example: 'in exercitation esse'.
            signAndEncryptKeyPairs (object): signAndEncryptKeyPairs
                Example:
                ```json
                {
                  "emailAddress": "aliquip quis id",
                  "primaryKeyPairId": "in exercitation esse",
                  "signAndEncryptKeyPairs": {
                    "encryptionKeyPairId": "elit nulla esse ut",
                    "signingKeyPairId": "est deserunt"
                  }
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            settings, CSE Identites
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if emailAddress is None:
            raise ValueError("Missing required parameter 'emailAddress'")
        request_body = {
            'emailAddress': emailAddress,
            'primaryKeyPairId': primaryKeyPairId,
            'signAndEncryptKeyPairs': signAndEncryptKeyPairs,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/cse/identities/{emailAddress}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._patch(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_cse_idenetites(self, userId, cseEmailAddress, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        GET CSE Idenetites

        Args:
            userId (string): userId
            cseEmailAddress (string): cseEmailAddress
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
            settings, CSE Identites
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if cseEmailAddress is None:
            raise ValueError("Missing required parameter 'cseEmailAddress'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/cse/identities/{cseEmailAddress}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def delete_cse_idenities(self, userId, cseEmailAddress, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> Any:
        """
        Delete CSE Idenities

        Args:
            userId (string): userId
            cseEmailAddress (string): cseEmailAddress
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
            settings, CSE Identites
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if cseEmailAddress is None:
            raise ValueError("Missing required parameter 'cseEmailAddress'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/cse/identities/{cseEmailAddress}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._delete(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_filters(self, userId, id, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Get Filters

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
        Delete Filters

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
        List Filters

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
        Create Filters

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

    def get_forwarding_addresses(self, userId, forwardingEmail, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Get Forwarding Addresses

        Args:
            userId (string): userId
            forwardingEmail (string): forwardingEmail
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
            settings, Forwarding Addresses
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if forwardingEmail is None:
            raise ValueError("Missing required parameter 'forwardingEmail'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/forwardingAddresses/{forwardingEmail}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def delete_forwarding_addresses(self, userId, forwardingEmail, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> Any:
        """
        Delete Forwarding Addresses

        Args:
            userId (string): userId
            forwardingEmail (string): forwardingEmail
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
            settings, Forwarding Addresses
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if forwardingEmail is None:
            raise ValueError("Missing required parameter 'forwardingEmail'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/forwardingAddresses/{forwardingEmail}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._delete(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def list_forwarding_addresses(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        List Forwarding Addresses

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
            settings, Forwarding Addresses
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/forwardingAddresses"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def create_forwarding_address(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, forwardingEmail=None, verificationStatus=None) -> dict[str, Any]:
        """
        Create Forwarding Address

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
            forwardingEmail (string): forwardingEmail Example: 'ad tempor dolor'.
            verificationStatus (string): verificationStatus
                Example:
                ```json
                {
                  "forwardingEmail": "ad tempor dolor",
                  "verificationStatus": "pending"
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            settings, Forwarding Addresses
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        request_body = {
            'forwardingEmail': forwardingEmail,
            'verificationStatus': verificationStatus,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/forwardingAddresses"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._post(url, data=request_body, params=query_params)
        response.raise_for_status()
        return response.json()

    def get_delegates(self, userId, delegateEmail, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        Get Delegates

        Args:
            userId (string): userId
            delegateEmail (string): delegateEmail
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
            settings, Delegates
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if delegateEmail is None:
            raise ValueError("Missing required parameter 'delegateEmail'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/delegates/{delegateEmail}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def delete_delegates(self, userId, delegateEmail, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> Any:
        """
        Delete Delegates

        Args:
            userId (string): userId
            delegateEmail (string): delegateEmail
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
            settings, Delegates
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        if delegateEmail is None:
            raise ValueError("Missing required parameter 'delegateEmail'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/delegates/{delegateEmail}"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._delete(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def list_delegates(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None) -> dict[str, Any]:
        """
        List Delegates

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
            settings, Delegates
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/delegates"
        query_params = {k: v for k, v in [('access_token', access_token), ('alt', alt), ('callback', callback), ('fields', fields), ('key', key), ('oauth_token', oauth_token), ('prettyPrint', prettyPrint), ('quotaUser', quotaUser), ('upload_protocol', upload_protocol), ('uploadType', uploadType), ('$.xgafv', xgafv)] if v is not None}
        response = self._get(url, params=query_params)
        response.raise_for_status()
        return response.json()

    def create_delegates(self, userId, access_token=None, alt=None, callback=None, fields=None, key=None, oauth_token=None, prettyPrint=None, quotaUser=None, upload_protocol=None, uploadType=None, xgafv=None, delegateEmail=None, verificationStatus=None) -> dict[str, Any]:
        """
        Create Delegates

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
            delegateEmail (string): delegateEmail Example: 'Duis commodo enim irure'.
            verificationStatus (string): verificationStatus
                Example:
                ```json
                {
                  "delegateEmail": "Duis commodo enim irure",
                  "verificationStatus": "rejected"
                }
                ```

        Returns:
            dict[str, Any]: Successful response

        Tags:
            settings, Delegates
        """
        if userId is None:
            raise ValueError("Missing required parameter 'userId'")
        request_body = {
            'delegateEmail': delegateEmail,
            'verificationStatus': verificationStatus,
        }
        request_body = {k: v for k, v in request_body.items() if v is not None}
        url = f"{self.base_url}/gmail/v1/users/{userId}/settings/delegates"
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
            self.watch_users,
            self.stop_notifications_for_user,
            self.send_drafts,
            self.get_drafts,
            self.update_drafts,
            self.delete_drafts,
            self.create_drafts,
            self.list_history,
            self.trash_messsages,
            self.untrash_messages,
            self.modify_messages,
            self.batch_delete,
            self.import_messages,
            self.send_messages,
            self.batch_modify,
            self.insert_messages,
            self.get_messages,
            self.delete_messages,
            self.get_attachments,
            self.create_labels,
            self.get_labels,
            self.update_labels,
            self.delete_labels,
            self.patch_labels,
            self.get_threads,
            self.delete_threads,
            self.modify_threads,
            self.trash_threads,
            self.list_threads,
            self.get_imap,
            self.update_imap,
            self.get_pop_settings,
            self.update_pop_settings,
            self.get_vacation_settings,
            self.update_vacation_settings,
            self.get_language_settings,
            self.update_language_settings,
            self.get_auto_forwarding_settings,
            self.update_auto_forwarding,
            self.set_default_smime_config,
            self.get_send_as_smime_info,
            self.delete_send_as_smime_info,
            self.list_smime_info,
            self.insert_smime_info,
            self.verify_send_as,
            self.get_send_as,
            self.update_send_as_setting,
            self.delete_send_as,
            self.patch_send_as,
            self.get_send_as1,
            self.create_send_as,
            self.get_cse_keypairs,
            self.list_cse_keypairs,
            self.create_cse_keypairs,
            self.list_cse_identites,
            self.create_cse_identites,
            self.patch_cse_identites,
            self.get_cse_idenetites,
            self.delete_cse_idenities,
            self.get_filters,
            self.delete_filters,
            self.list_filters,
            self.create_filters,
            self.get_forwarding_addresses,
            self.delete_forwarding_addresses,
            self.list_forwarding_addresses,
            self.create_forwarding_address,
            self.get_delegates,
            self.delete_delegates,
            self.list_delegates,
            self.create_delegates
        ]
