import * as crypto from 'crypto';

export interface ApprovalToken {
  token: string;
  proposalId: string;
  workspaceId: string;
  baseRevision: number;
  timestamp: number;
  used: boolean;
}

export class ApprovalTokenManager {
  private static tokens: Map<string, ApprovalToken> = new Map();

  /**
   * Generates a single-use approval token bound to exact proposal, workspace, and revision.
   */
  public static generateToken(proposalId: string, workspaceId: string, baseRevision: number): ApprovalToken {
    const randomBytes = Math.random().toString(36).substring(2, 10);
    const tokenString = `auth_tok_${proposalId}_${baseRevision}_${randomBytes}`;

    const token: ApprovalToken = {
      token: tokenString,
      proposalId,
      workspaceId,
      baseRevision,
      timestamp: Date.now(),
      used: false
    };

    ApprovalTokenManager.tokens.set(tokenString, token);
    return { ...token };
  }

  /**
   * Verifies and consumes the single-use approval token.
   * Fails if token is missing, already used, or mismatched against target proposal.
   */
  public static verifyAndConsumeToken(
    tokenString: string,
    expectedProposalId: string,
    expectedWorkspaceId: string,
    expectedBaseRevision: number
  ): { valid: boolean; error?: string } {
    const tokenObj = ApprovalTokenManager.tokens.get(tokenString);

    if (!tokenObj) {
      return { valid: false, error: 'Authorization token not found or invalid' };
    }

    if (tokenObj.used) {
      return { valid: false, error: 'SECURITY VIOLATION: Approval token has already been consumed (Duplicate execution attempt)' };
    }

    if (tokenObj.proposalId !== expectedProposalId) {
      return { valid: false, error: `Token proposal ID mismatch: expected ${expectedProposalId}, got ${tokenObj.proposalId}` };
    }

    if (tokenObj.workspaceId !== expectedWorkspaceId) {
      return { valid: false, error: `Token workspace ID mismatch: expected ${expectedWorkspaceId}, got ${tokenObj.workspaceId}` };
    }

    if (tokenObj.baseRevision !== expectedBaseRevision) {
      return { valid: false, error: `Token revision mismatch: expected ${expectedBaseRevision}, got ${tokenObj.baseRevision}` };
    }

    // Token is valid -> Mark consumed
    tokenObj.used = true;
    return { valid: true };
  }
}
